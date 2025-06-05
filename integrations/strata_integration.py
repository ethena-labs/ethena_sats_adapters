import logging
import json
from copy import deepcopy
from typing import Dict, List, Optional, Set
from eth_typing import ChecksumAddress
from web3 import Web3
from constants.chains import Chain
from constants.example_integrations import PAGINATION_SIZE
from constants.summary_columns import SummaryColumn
from constants.strata import (
    STRATA_MAINNET, STRATA_TESTNET
)
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import (
    ETH_NODE_URL,
    call_with_retry,
    fetch_events_logs_with_retry,
)

ERC4626_ABI = json.loads(open("abi/ERC4626_abi.json").read())


class StrataIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID = IntegrationID.STRATA_MONEY_PREDEPOSIT,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = [SummaryColumn.STRATA_MONEY_PREDEPOSIT],
        reward_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        rpc = ETH_NODE_URL,
        strata = STRATA_MAINNET,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=strata["pUSDe"]["block"],
            chain=chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            excluded_addresses=excluded_addresses
        )
        # Initialize Web3 provider - use ETH_NODE_URL from environment variables
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        if not self.w3.is_connected():
            logging.error(f"Failed to connect to RPC at {ETH_NODE_URL}")
            raise ConnectionError(f"Could not connect to Ethereum RPC at {ETH_NODE_URL}")
        logging.info(f"Connected to Ethereum RPC at {ETH_NODE_URL}")

        # Initialize pUSDe contract
        self.token_contract = self.w3.eth.contract(
            address=strata["pUSDe"]["address"],
            abi=ERC4626_ABI,
        )


    def get_balance(self, user: str, block: int) -> float:
        pUSDe_balance = call_with_retry(
            self.token_contract.functions.balanceOf(Web3.to_checksum_address(user)), block = block
        )
        USDe_balance = call_with_retry(
            self.token_contract.functions.convertToAssets(pUSDe_balance), block = block
        )
        return USDe_balance



    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """
        Get user balances for specified blocks, using cached data when available.

        Args:
            cached_data: Dictionary mapping block numbers to user balances at that block
            blocks: List of block numbers to get balances for

        Returns:
            Dictionary mapping block numbers to user balances at that block
        """
        logging.info("[Strata integration] Getting block balances")

        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            return new_block_data

        blocks = sorted(blocks)

        if (self.token_contract.address == "0x0000000000000000000000000000000000000000"):
            empty_results = {key: {} for key in blocks}
            return empty_results

        cache_copy: Dict[int, Dict[ChecksumAddress, float]] = deepcopy(cached_data)
        for block in blocks:
            # find the closest prev block in the data
            # list keys parsed as ints and in descending order
            sorted_existing_blocks = sorted(
                cache_copy,
                reverse=True,
            )
            # loop through the sorted blocks and find the closest previous block
            prev_block = self.start_block
            start = prev_block
            balances = {}
            for existing_block in sorted_existing_blocks:
                if existing_block < block:
                    prev_block = existing_block
                    start = existing_block + 1
                    balances = deepcopy(cache_copy[prev_block])
                    break
            # parse transfer events since and update balances
            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)
                # print(f"Fetching transfers from {start} to {to_block}")
                transfers = fetch_events_logs_with_retry(
                    "pUSDe Token transfers",
                    self.token_contract.events.Transfer(),
                    start,
                    to_block,
                )
                for transfer in transfers:
                    sender = transfer["args"]["from"]
                    recipient = transfer["args"]["to"]
                    if recipient not in balances:
                        balances[recipient] = 0
                    if sender not in balances:
                        balances[sender] = 0

                    amount = round(transfer["args"]["value"] / 10**18, 6)
                    balances[sender] -= max(amount, balances[sender])
                    balances[recipient] += amount

                start = to_block + 1

            balances.pop('0x0000000000000000000000000000000000000000', None)
            new_block_data[block] = balances
            cache_copy[block] = balances
        return new_block_data


if __name__ == "__main__":
    example_integration = StrataIntegration(
        rpc = STRATA_TESTNET["RPC"],
        strata = STRATA_TESTNET
    )

    current_block = example_integration.w3.eth.get_block_number()
    # Without cached data
    without_cached_data_output = example_integration.get_block_balances(
        cached_data={}, blocks=[ current_block - 1000 ]
    )

    print("=" * 120)
    print("Run without cached data", without_cached_data_output)
    print("=" * 120)

    # With cached data, using the previous output so there is no need
    # to fetch the previous blocks again
    with_cached_data_output = example_integration.get_block_balances(
        cached_data=without_cached_data_output, blocks=[current_block]
    )
    print("Run with cached data", with_cached_data_output)
    print("=" * 120)

    user = next(iter(with_cached_data_output[current_block]))
    balance_output = example_integration.get_balance(
        user=user, block=int(current_block)
    )
    print("User USDe balance", balance_output)

    mainnet_integration = StrataIntegration(
        strata = STRATA_MAINNET
    )
    mainnet_balance_output = mainnet_integration.get_block_balances(
        cached_data={}, blocks=[ current_block - 1000 ]
    )
    print("Mainnet balances", mainnet_balance_output)
