import logging
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from web3 import Web3
from eth_typing import ChecksumAddress
from eth_abi.abi import decode
import os

# Attempt to import project-specific modules.
try:
    from constants.hyperlend import (
        HYPERLEND_MAIN_CONTRACT,
        HYPERLEND_DATA_PROVIDER,
        HYPERLEND_PROVIDER,
        USDE_TOKEN_ADDRESS,
        HYPERLEND_START_BLOCK,
        MAIN_CONTRACT_ABI,
        DATA_PROVIDER_ABI,
        MULTICALL_ABI,
    )
    from integrations.cached_balances_integration import CachedBalancesIntegration
    from integrations.integration_ids import IntegrationID
    from constants.summary_columns import SummaryColumn
    from constants.chains import Chain
    from utils.web3_utils import multicall_by_address
except ModuleNotFoundError:
    import sys
    import os

    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_dir = os.path.dirname(current_script_dir)
    if project_root_dir not in sys.path:
        sys.path.insert(0, project_root_dir)

    from constants.hyperlend import (
        HYPERLEND_MAIN_CONTRACT,
        HYPERLEND_DATA_PROVIDER,
        HYPERLEND_PROVIDER,
        USDE_TOKEN_ADDRESS,
        HYPERLEND_START_BLOCK,
        MAIN_CONTRACT_ABI,
        DATA_PROVIDER_ABI,
        MULTICALL_ABI,
    )
    from integrations.cached_balances_integration import CachedBalancesIntegration
    from integrations.integration_ids import IntegrationID
    from constants.summary_columns import SummaryColumn
    from constants.chains import Chain
    from utils.web3_utils import multicall_by_address

logger = logging.getLogger(__name__)


# Custom multicall implementation using MULTICALL_ABI from hyperlend.py directly
def custom_multicall_by_address(
    w3: Web3,
    multicall_address: str,
    calls: List[Tuple[Any, str, List[Any]]],
    block_identifier: Union[int, str] = "latest",
) -> List[Any]:
    """
    Custom implementation of multicall using the HyperLend specific ABI

    Args:
        w3: Web3 instance
        multicall_address: The address of the multicall contract
        calls: List of tuples containing (contract, function_name, args)
        block_identifier: Block number or identifier to query

    Returns:
        List of decoded results from each contract call
    """
    multicall_contract = w3.eth.contract(
        address=Web3.to_checksum_address(multicall_address), abi=MULTICALL_ABI
    )

    aggregate_calls = []
    for call in calls:
        contract, fn_name, args = call
        call_data = contract.encode_abi(fn_name=fn_name, args=args)
        aggregate_calls.append((contract.address, call_data))

    _block_number, return_data_list = multicall_contract.functions.aggregate(
        aggregate_calls
    ).call(block_identifier=block_identifier)

    # Helper function to handle nested tuple types
    def collapse_if_tuple(abi_type):
        if abi_type["type"].startswith("tuple"):
            # Process tuple components
            components = [collapse_if_tuple(comp) for comp in abi_type["components"]]
            typ = f"({','.join(components)})"
            # Handle tuple arrays like tuple[] or tuple[2][]
            if abi_type["type"].endswith("[]"):
                return typ + "[]"
            elif "[]" in abi_type["type"]:
                array_spec = abi_type["type"][5:]  # get array dimensions e.g. [2][]
                return typ + array_spec
            else:
                return typ
        else:
            return abi_type["type"]

    decoded_results = []
    for i, call in enumerate(calls):
        contract, fn_name, _ = call
        function = contract.get_function_by_name(fn_name)
        try:
            # Extract output types, properly handling tuples
            output_types = [
                collapse_if_tuple(output) for output in function.abi["outputs"]
            ]
            # Decode using eth_abi's decode function with properly formatted output types
            decoded_results.append(decode(output_types, return_data_list[i]))
        except Exception as e:
            decoded_results.append(None)

    return decoded_results


MINIMAL_ERC20_TRANSFER_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
]
NULL_ADDRESS = "0x0000000000000000000000000000000000000000"
LOG_QUERY_BLOCK_CHUNK_SIZE = 10000  # Chunk size for fetching logs
RAY = int(1e27)  # For liquidity index calculations

HYPEREVM_NETWORK_MULTICALL_ADDRESS_STR: Optional[str] = (
    "0xca11bde05977b3631167028862be2a173976ca11"  # SET THIS!
)


class HyperlendUsdeIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block_override: Optional[int] = None,
        start_block_override: Optional[int] = None,
    ):
        self.hyperlend_onchain_start_block = HYPERLEND_START_BLOCK
        effective_start_block = (
            start_block_override
            if start_block_override is not None
            else self.hyperlend_onchain_start_block
        )

        # Track the latest block that we've indexed events for
        self.last_indexed_block = (
            effective_start_block - 1
        )  # Start with no blocks indexed
        # Keep track of all known participants across all blocks - this allows us to track
        # new users that appear in new events
        self.all_known_participants: Set[str] = set()

        try:
            self.chain_for_framework = Chain.HYPEREVM
        except AttributeError:
            self.chain_for_framework = Chain.ETHEREUM

        effective_summary_cols = summary_cols
        if effective_summary_cols is None:
            try:
                effective_summary_cols = [SummaryColumn.TEMPLATE_PTS]
            except AttributeError:
                effective_summary_cols = []

        super().__init__(
            integration_id=integration_id,
            start_block=effective_start_block,
            chain=self.chain_for_framework,
            summary_cols=effective_summary_cols,
            reward_multiplier=reward_multiplier,
            balance_multiplier=balance_multiplier,
            excluded_addresses=excluded_addresses,
            end_block=end_block_override,
        )

        # Safeguard: Ensure self.cached_balances is initialized by the parent, or initialize it here.
        if not hasattr(self, "cached_balances") or self.cached_balances is None:
            self.cached_balances: Dict[int, Dict[ChecksumAddress, float]] = {}

        self.rpc_url = os.getenv("HYPEREVM_NODE_URL") #"https://rpc.hyperlend.finance/archive"
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(
                    f"Failed to connect to Web3 provider at {self.rpc_url}"
                )
        except Exception as e:
            raise

        self.main_contract_address = Web3.to_checksum_address(HYPERLEND_MAIN_CONTRACT)
        self.main_contract_abi = MAIN_CONTRACT_ABI
        self.main_contract = self.w3.eth.contract(
            address=self.main_contract_address, abi=self.main_contract_abi
        )

        self.data_provider_address = Web3.to_checksum_address(HYPERLEND_DATA_PROVIDER)
        self.data_provider_abi = DATA_PROVIDER_ABI
        self.data_provider_contract = self.w3.eth.contract(
            address=self.data_provider_address, abi=self.data_provider_abi
        )

        self.usde_token_address = Web3.to_checksum_address(USDE_TOKEN_ADDRESS)
        self.husde_token_contract = self.w3.eth.contract(
            address=self.usde_token_address, abi=MINIMAL_ERC20_TRANSFER_ABI
        )

        self.hyperlend_provider_for_balances = Web3.to_checksum_address(
            HYPERLEND_PROVIDER
        )
        self.usde_decimals = 18

        self.hyperevm_specific_multicall_address: Optional[ChecksumAddress] = None
        if HYPEREVM_NETWORK_MULTICALL_ADDRESS_STR:
            try:
                self.hyperevm_specific_multicall_address = Web3.to_checksum_address(
                    HYPEREVM_NETWORK_MULTICALL_ADDRESS_STR
                )
            except ValueError:
                pass
        else:
            pass

    def _fetch_participants_in_range(
        self, start_block: int, end_block: int
    ) -> Set[str]:
        all_users: Set[str] = set()
        event_details = [
            ("Supply", ["onBehalfOf"]),
            ("Withdraw", ["user", "to"]),
            ("Borrow", ["onBehalfOf"]),
            ("Repay", ["user", "repayer"]),
        ]

        for event_name_str, user_arg_names in event_details:
            current_event_block_start = start_block
            while current_event_block_start <= end_block:
                current_event_block_end = min(
                    current_event_block_start + LOG_QUERY_BLOCK_CHUNK_SIZE - 1,
                    end_block,
                )
                try:
                    event_filter_obj = getattr(
                        self.main_contract.events, event_name_str
                    )
                    logs = event_filter_obj.get_logs(
                        fromBlock=current_event_block_start,  # Changed from from_block
                        toBlock=current_event_block_end,  # Changed from to_block
                        argument_filters={"reserve": self.usde_token_address},
                    )
                    for log_entry in logs:
                        for arg_name in user_arg_names:
                            if arg_name in log_entry["args"]:
                                all_users.add(log_entry["args"][arg_name])
                except ValueError as ve:
                    if (
                        "query exceeds max results" in str(ve).lower()
                        or "response size exceeded" in str(ve).lower()
                        or "block range" in str(ve).lower()
                    ):
                        pass
                    else:
                        raise
                except Exception as e:
                    raise
                current_event_block_start = current_event_block_end + 1

        current_block_start = start_block
        while current_block_start <= end_block:
            current_block_end = min(
                current_block_start + LOG_QUERY_BLOCK_CHUNK_SIZE - 1, end_block
            )
            try:
                transfer_event_filter = (
                    self.husde_token_contract.events.Transfer.get_logs(
                        fromBlock=current_block_start,  # Changed from from_block
                        toBlock=current_block_end,  # Changed from to_block
                    )
                )
                for log_entry in transfer_event_filter:
                    from_address = log_entry["args"].get("from")
                    to_address = log_entry["args"].get("to")
                    if (
                        from_address
                        and Web3.to_checksum_address(from_address) != NULL_ADDRESS
                    ):
                        all_users.add(from_address)
                    if (
                        to_address
                        and Web3.to_checksum_address(to_address) != NULL_ADDRESS
                    ):
                        all_users.add(to_address)
            except ValueError as ve:
                if (
                    "query exceeds max results" in str(ve).lower()
                    or "response size exceeded" in str(ve).lower()
                ):
                    pass
                else:
                    raise
            except Exception as e:
                raise
            current_block_start = current_block_end + 1

        return all_users

    def get_block_balances(  # Ensure method is named get_block_balances and handles caching
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        final_results: Dict[int, Dict[ChecksumAddress, float]] = {}
        blocks_to_fetch_live: List[int] = []

        for block_num in sorted(
            list(set(blocks))
        ):  # Use set to handle potential duplicate blocks
            if block_num < self.start_block:
                final_results[block_num] = {}
                continue

            if block_num in self.cached_balances:
                final_results[block_num] = self.cached_balances[block_num]
            else:
                blocks_to_fetch_live.append(block_num)

        if not blocks_to_fetch_live:
            return final_results

        min_live_block = min(blocks_to_fetch_live)
        max_live_block = max(blocks_to_fetch_live)

        if max_live_block <= self.last_indexed_block:
            all_potential_participants_set = self.all_known_participants.copy()
        else:
            participant_scan_start_block = self.last_indexed_block + 1
            participant_scan_end_block = max_live_block

            new_participants_set = self._fetch_participants_in_range(
                start_block=participant_scan_start_block,
                end_block=participant_scan_end_block,
            )

            self.all_known_participants.update(new_participants_set)
            self.last_indexed_block = max_live_block

            all_potential_participants_set = self.all_known_participants.copy()

        if not all_potential_participants_set:
            for block_num_live in blocks_to_fetch_live:
                self.cached_balances[block_num_live] = {}  # Update cache
                final_results[block_num_live] = {}
            return final_results

        all_potential_participants_list = [
            Web3.to_checksum_address(addr)
            for addr in all_potential_participants_set
            if addr
        ]

        for block_num_live in blocks_to_fetch_live:
            if block_num_live < self.start_block:
                self.cached_balances[block_num_live] = {}  # Update cache
                final_results[block_num_live] = {}
                continue

            balances_at_block_live: Dict[ChecksumAddress, float] = {}

            if not all_potential_participants_list:
                self.cached_balances[block_num_live] = {}  # Update cache
                final_results[block_num_live] = {}
                continue

            if not self.hyperevm_specific_multicall_address:
                self.cached_balances[block_num_live] = {}  # Update cache
                final_results[block_num_live] = {}
                continue

            liquidity_index_usde: Optional[int] = None
            try:
                reserve_data_usde = self.main_contract.functions.getReserveData(
                    self.usde_token_address
                ).call(block_identifier=block_num_live)

                if reserve_data_usde and len(reserve_data_usde) > 1:
                    liquidity_index_usde = reserve_data_usde[
                        1
                    ]  # liquidityIndex is the second element
                else:
                    self.cached_balances[block_num_live] = {}
                    final_results[block_num_live] = {}
                    continue

            except Exception as e:
                self.cached_balances[block_num_live] = {}
                final_results[block_num_live] = {}
                continue

            if liquidity_index_usde is None:
                self.cached_balances[block_num_live] = {}
                final_results[block_num_live] = {}
                continue

            MULTICALL_PARTICIPANT_BATCH_SIZE = 350
            aggregated_multicall_results = []

            try:
                for i in range(
                    0,
                    len(all_potential_participants_list),
                    MULTICALL_PARTICIPANT_BATCH_SIZE,
                ):
                    participant_chunk = all_potential_participants_list[
                        i : i + MULTICALL_PARTICIPANT_BATCH_SIZE
                    ]
                    if not participant_chunk:
                        continue

                    calls_for_multicall_chunk = []
                    for user_checksum_address in participant_chunk:
                        calls_for_multicall_chunk.append(
                            (
                                self.data_provider_contract,
                                "getUserReservesData",
                                [
                                    self.hyperlend_provider_for_balances,
                                    user_checksum_address,
                                ],
                            )
                        )

                    chunk_results = custom_multicall_by_address(
                        self.w3,
                        self.hyperevm_specific_multicall_address,
                        calls_for_multicall_chunk,
                        block_identifier=block_num_live,
                    )
                    aggregated_multicall_results.extend(chunk_results)

                for i, user_checksum_address in enumerate(
                    all_potential_participants_list
                ):
                    if i < len(aggregated_multicall_results):
                        raw_user_reserves_data = aggregated_multicall_results[i]

                        if (
                            raw_user_reserves_data
                            and raw_user_reserves_data is not None
                        ):
                            if (
                                isinstance(raw_user_reserves_data, tuple)
                                and len(raw_user_reserves_data) > 0
                            ):
                                user_reserves_list = raw_user_reserves_data[0]

                                found_usde_for_user = False
                                for reserve_data in user_reserves_list:
                                    underlying_asset = reserve_data[0]

                                    if (
                                        Web3.to_checksum_address(underlying_asset)
                                        == self.usde_token_address
                                    ):
                                        scaledATokenBalance = reserve_data[1]

                                        adjusted_scaled_balance = (
                                            scaledATokenBalance * liquidity_index_usde
                                        ) // RAY

                                        float_balance = float(
                                            adjusted_scaled_balance
                                            / (10**self.usde_decimals)
                                        )

                                        if float_balance > 0.0:
                                            balances_at_block_live[
                                                user_checksum_address
                                            ] = float_balance

                                        found_usde_for_user = True
                                        break
                    else:
                        break

            except Exception as e:
                self.cached_balances[block_num_live] = {}  # Cache empty on error
                final_results[block_num_live] = {}
                continue

            self.cached_balances[block_num_live] = (
                balances_at_block_live  # Update cache with fetched data
            )
            final_results[block_num_live] = balances_at_block_live

        return final_results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)  # Ensure logger is defined for the main block

    # Ensure IntegrationID and HYPERLEND_START_BLOCK are available
    # These are expected to be imported by the try-except block at the top of the file.
    try:
        _ = IntegrationID
        _ = HYPERLEND_START_BLOCK
    except NameError:
        logger.error(
            "IntegrationID or HYPERLEND_START_BLOCK not found. Ensure imports are correct at the top of the script."
        )
        import sys

        sys.exit(1)

    if HYPEREVM_NETWORK_MULTICALL_ADDRESS_STR:
        logger.info(
            f"Attempting to use Hyperevm Multicall Address: {HYPEREVM_NETWORK_MULTICALL_ADDRESS_STR}"
        )
    else:
        logger.warning(
            "HYPEREVM_NETWORK_MULTICALL_ADDRESS_STR is not set in the script. Multicall will be skipped."
        )

    logger.info(
        "Starting HyperLend USDe Integration Script (Advanced Test Run with Cache Verification)"
    )

    try:
        integration_id_to_use = IntegrationID.HYPERLEND_USDE
        integration_instance = HyperlendUsdeIntegration(
            integration_id=integration_id_to_use
        )
        logger.info(
            f"Successfully instantiated HyperlendUsdeIntegration with ID: {integration_id_to_use.value if hasattr(integration_id_to_use, 'value') else integration_id_to_use}"
        )

        # Determine blocks to query
        latest_block = integration_instance.w3.eth.block_number
        logger.info(f"Latest block on HyperEVM network: {latest_block}")

        blocks_to_query = sorted(
            list(
                set(
                    [
                        HYPERLEND_START_BLOCK,
                        HYPERLEND_START_BLOCK + 1,
                        HYPERLEND_START_BLOCK + 2,
                        latest_block - 5000,  # Query all blocks up to some recent one
                    ]
                )
            )
        )

        logger.info(f"Preparing to query balances for blocks: {blocks_to_query}")

        # --- First call (populating the cache) ---
        logger.info("--- First call to get_block_balances (populating cache) ---")
        balances_first_call = integration_instance.get_block_balances(
            cached_data={}, blocks=blocks_to_query
        )

        if balances_first_call:
            logger.info("Fetched balances (first call):")
            for block, user_balances in balances_first_call.items():
                if user_balances:
                    logger.info(f"  Block {block}:")
                    for user, balance in user_balances.items():
                        logger.info(f"    User: {user}, Balance: {balance}")
                else:
                    logger.info(
                        f"  Block {block}: No USDe balances found (first call)."
                    )
        else:
            logger.info(
                "No balance data returned from the first call."
            )  # --- Second call (testing the cache with both cached and non-cached blocks) ---
        logger.info(
            "--- Second call to get_block_balances (testing cache with mixed blocks) ---"
        )

        new_blocks = [HYPERLEND_START_BLOCK + 3, HYPERLEND_START_BLOCK + 4]

        mixed_blocks_to_query = sorted(list(set(blocks_to_query + new_blocks)))
        logger.info(
            f"Preparing to query mixed blocks (cached + non-cached): {mixed_blocks_to_query}"
        )
        logger.info(f"Previously cached blocks: {blocks_to_query}")
        logger.info(f"New non-cached blocks: {new_blocks}")

        logger.info(
            f"Last indexed block before second call: {integration_instance.last_indexed_block}"
        )
        logger.info(
            f"Total known participants before second call: {len(integration_instance.all_known_participants)}"
        )

        balances_second_call = integration_instance.get_block_balances(
            cached_data={}, blocks=mixed_blocks_to_query
        )

        logger.info(
            f"Last indexed block after second call: {integration_instance.last_indexed_block}"
        )
        logger.info(
            f"Total known participants after second call: {len(integration_instance.all_known_participants)}"
        )

        if balances_second_call:
            logger.info(
                "Fetched balances (second call - mixed cached and non-cached blocks):"
            )
            for block, user_balances in balances_second_call.items():
                cache_status = "cached" if block in blocks_to_query else "newly fetched"
                if user_balances:
                    logger.info(f"  Block {block} ({cache_status}):")
                    for user, balance in user_balances.items():
                        logger.info(f"    User: {user}, Balance: {balance}")
                else:
                    logger.info(
                        f"  Block {block} ({cache_status}): No USDe balances found (second call)."
                    )
        else:
            logger.info(
                "No balance data returned from the second call."
            )  # --- Verification ---
        logger.info("--- Cache Verification ---")

        cached_blocks_match = True
        for block in blocks_to_query:
            if balances_first_call.get(block) != balances_second_call.get(block):
                cached_blocks_match = False
                logger.error(f"Mismatch found for previously cached block {block}:")
                logger.error(f"  First call: {balances_first_call.get(block)}")
                logger.error(f"  Second call: {balances_second_call.get(block)}")

        if cached_blocks_match:
            logger.info(
                "SUCCESS: Results from the first call match with the cached blocks in the second call. Cache retrieval works correctly."
            )
        else:
            logger.error(
                "FAILURE: Results from the first call differ from cached blocks in the second call. Cache retrieval may not be working as expected."
            )

        new_blocks_properly_fetched = True
        for block in new_blocks:
            if block not in balances_second_call:
                new_blocks_properly_fetched = False
                logger.error(
                    f"New block {block} is missing from the second call results."
                )
            elif not isinstance(balances_second_call.get(block), dict):
                new_blocks_properly_fetched = False
                logger.error(
                    f"New block {block} does not have a proper dictionary of balances in the second call."
                )

        if new_blocks_properly_fetched:
            logger.info(
                "SUCCESS: New non-cached blocks were properly fetched in the second call."
            )
        else:
            logger.error(
                "FAILURE: Some new non-cached blocks were not properly fetched in the second call."
            )

        logger.info(
            f"Current cache state after all calls (should include both original and new blocks): {integration_instance.cached_balances}"
        )

        logger.info(
            "--- Third call to get_block_balances (testing optimized event indexing) ---"
        )

        intermediate_block = HYPERLEND_START_BLOCK + 3

        logger.info(
            f"Testing optimized indexing with intermediate block: {intermediate_block}"
        )
        logger.info(
            f"Last indexed block before third call: {integration_instance.last_indexed_block}"
        )
        logger.info(
            f"Since {intermediate_block} <= {integration_instance.last_indexed_block}, no new event scanning should occur"
        )

        balances_third_call = integration_instance.get_block_balances(
            cached_data={}, blocks=[intermediate_block]
        )

        if intermediate_block in balances_third_call:
            logger.info(
                f"Successfully fetched balances for block {intermediate_block} without new event scanning"
            )
            logger.info(
                f"Found {len(balances_third_call[intermediate_block])} users with balances"
            )
        else:
            logger.error(
                f"Failed to fetch balances for intermediate block {intermediate_block}"
            )

        logger.info(
            f"Last indexed block after third call: {integration_instance.last_indexed_block}"
        )
        logger.info(
            f"Total known participants after third call: {len(integration_instance.all_known_participants)}"
        )

        current_block = latest_block

        logger.info(
            f"Testing with latest block call {current_block} > last indexed block {integration_instance.last_indexed_block}"
        )
        logger.info("This should trigger new event scanning")

        balances_future_call = integration_instance.get_block_balances(
            cached_data={}, blocks=[current_block]
        )

        logger.info(
            f"Last indexed block after latest block call: {integration_instance.last_indexed_block}"
        )
        logger.info(
            f"Total known participants after latest block call: {len(integration_instance.all_known_participants)}"
        )

    except AttributeError as ae:
        if "IntegrationID" in str(ae) and "HYPERLEND_USDE" in str(ae):
            logger.error(
                f"AttributeError: {ae}. '{integration_id_to_use}' might not be a defined member of IntegrationID."
            )
            logger.error(
                "Please ensure the IntegrationID is defined in 'integrations/integration_ids.py' or use an existing/valid ID."
            )
        else:
            logger.error(f"An AttributeError occurred: {ae}", exc_info=True)
    except Exception as e:
        logger.error(f"An error occurred during the test run: {e}", exc_info=True)
