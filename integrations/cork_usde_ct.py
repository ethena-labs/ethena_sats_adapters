import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, NamedTuple

from web3 import Web3
from eth_typing import ChecksumAddress, AnyAddress

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from constants.cork import (
    USDE_TOKEN_ADDRESS_BY_CHAIN,
    PSM_USDE_START_BLOCK_BY_CHAIN,
    LV_ADDRESS_BY_CHAIN,
    PSM_CONTRACT_BY_CHAIN,
    PAGINATION_SIZE,
    ZERO_ADDRESS,
    ERC20_ABI,
    TokenType,
)

from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import fetch_events_logs_with_retry, W3_BY_CHAIN

@dataclass
class VaultBalance(NamedTuple):
    total_assets: int
    total_supply: int
    shares_by_account: Dict[AnyAddress, int] = {}

class TermConfig(NamedTuple):
    share_token_addr: ChecksumAddress

class PairConfig(NamedTuple):
    eligible_asset: TokenType
    terms: Dict[int, TermConfig] = {}


class CorkIntegration(
    CachedBalancesIntegration
):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block: Optional[int] = None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func: Optional[Callable[[int, str], int]] = None,
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            summary_cols,
            reward_multiplier,
            balance_multiplier,
            excluded_addresses,
            end_block,
            ethereal_multiplier,
            ethereal_multiplier_func,
        )

        self.w3 = W3_BY_CHAIN[self.chain]["w3"]
        self.psm_contract = PSM_CONTRACT_BY_CHAIN[self.chain]
        self.pair_config_by_id: Dict[bytes, PairConfig] = {}
        # self.term_config_by_id: Dict[bytes, Dict[int, TermConfig]] = {}

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Get user balances for specified blocks, using cached data when available.

        Args:
            cached_data (Dict[int, Dict[ChecksumAddress, float]]): Dictionary mapping block numbers
                to user balances at that block. Used to avoid recomputing known balances.
                The inner dictionary maps user addresses to their token balance.
            blocks (List[int]): List of block numbers to get balances for.

        Returns:
            Dict[int, Dict[ChecksumAddress, float]]: Dictionary mapping block numbers to user balances,
                where each inner dictionary maps user addresses to their token balance
                at that block.
        """
        logging.info("Getting block data for claimed USDe")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to get_block_balances")
            return new_block_data

        sorted_blocks = sorted(blocks)
        cache_copy_of_account_bals: Dict[int, Dict[ChecksumAddress, float]] = deepcopy(cached_data)

        for block in sorted_blocks:
            # find the closest prev block in the data
            # list keys parsed as ints and in descending order
            sorted_existing_blocks = sorted(
                cache_copy_of_account_bals,
                reverse=True,
            )

            # loop through the sorted blocks and find the closest previous block
            prev_block = self.start_block
            start = prev_block
            account_bals: Dict[AnyAddress, int] = {}
            vault_bals: Dict[ChecksumAddress, VaultBalance] = {}

            for existing_block in sorted_existing_blocks:
                if existing_block < block:
                    prev_block = existing_block
                    start = existing_block + 1
                    account_bals = deepcopy(cache_copy_of_account_bals[prev_block])
                    break

            # parse events since and update bals
            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)
                # print(f"Fetching events from {start} to {to_block}")

                # Fetch events that indicates new pair was created
                new_pair_events_with_eligible_pa = fetch_events_logs_with_retry(
                    "Pairs initialized with USDe as PA",
                    self.psm_contract.events.InitializedModuleCore(),
                    start,
                    to_block,
                    filter = {
                        "pa": USDE_TOKEN_ADDRESS_BY_CHAIN[self.chain],
                    },
                )
                new_pair_events_with_eligible_ra = fetch_events_logs_with_retry(
                    "Pairs initialized with USDe as RA",
                    self.psm_contract.events.InitializedModuleCore(),
                    start,
                    to_block,
                    filter = {
                        "ra": USDE_TOKEN_ADDRESS_BY_CHAIN[self.chain],
                    },
                )

                # /// @notice Emitted when a new LV and PSM is initialized with a given pair
                # /// @param id The PSM id
                # /// @param pa The address of the pegged asset
                # /// @param ra The address of the redemption asset
                # /// @param lv The address of the LV
                # /// @param expiry The expiry interval of the DS
                # event InitializedModuleCore(
                #     Id indexed id, address indexed pa, address indexed ra, address lv, uint256 expiry);
                # )

                # Add new pairs to config
                self.pair_config_by_id |= {
                    event["args"]["id"]: PairConfig(eligible_asset=TokenType.PA)
                    for event in new_pair_events_with_eligible_pa
                    # if event["args"]["pa"] == USDE_TOKEN_ADDRESS_BY_CHAIN[self.chain]
                } | {
                    event["args"]["id"]: PairConfig(eligible_asset=TokenType.RA)
                    for event in new_pair_events_with_eligible_ra
                    # if event["args"]["ra"] == USDE_TOKEN_ADDRESS_BY_CHAIN[self.chain]
                }

                # For each pair, update config...
                for pair_id, pair_config in self.pair_config_by_id.items():
                    # Fetch events that indicate a new term was issued/started
                    new_term_events_of_pair = fetch_events_logs_with_retry(
                        "Issuance on pairs with USDe",
                        self.psm_contract.events.Issued(),
                        start,
                        to_block,
                        filter = {
                            "id": pair_id,
                        },
                    )

                    # For each term, update config...
                    for new_term_event in new_term_events_of_pair:
                        # /// @notice Emitted when a new DS is issued for a given PSM
                        # /// @param id The PSM id
                        # /// @param dsId The DS id
                        # /// @param expiry The expiry of the DS
                        # /// @param ds The address of the DS token
                        # /// @param ct The address of the CT token
                        # /// @param raCtUniPairId The id of the uniswap-v4 pair between RA and CT
                        # event Issued(
                        #     Id indexed id, uint256 indexed dsId, uint256 indexed expiry, address ds, address ct, bytes32 raCtUniPairId
                        # )

                        # the `ds_id` identifies each term, but is not unique globally (across pairs)
                        term_id: int = new_term_event["args"]["dsId"]

                        # the `share_token_addr` is unique and only valid for each term (or issuance)
                        share_token_addr = Web3.to_checksum_address(new_term_event["args"]["ct"])

                        # Add new term to config
                        pair_config.terms.setdefault(term_id, TermConfig(share_token_addr=share_token_addr))
                        # self.term_config_by_id.setdefault(pair_id, {}).setdefault(term_id, TermConfig(share_token_addr=share_token_addr))
                    
                # For each pair...
                for pair_id, pair_config in self.pair_config_by_id.items():
                    # For each term, accumulate all changes on amount of assets locked in PSM...
                    for term_id, term_config in pair_config.terms.items():
                        # Fetch various events when assets are going IN or OUT of the PSM vault:

                        # event PsmDeposited(Id indexed id, uint256 indexed dsId, address indexed depositor, uint256 amount, uint256 received, uint256 exchangeRate)
                        # IN: RA
                        # OUT: DS + CT
                        deposit_events = fetch_events_logs_with_retry(
                            "Deposit on pairs with USDe",
                            self.psm_contract.events.PsmDeposited(),
                            start,
                            to_block,
                            filter = {
                                "id": pair_id,
                                "dsId": term_id,
                            },
                        )

                        # event CtRedeemed(Id indexed id, uint256 indexed dsId, address indexed redeemer, uint256 amount, uint256 paReceived, uint256 raReceived)
                        # IN: CT
                        # OUT: PA + RA
                        withdraw_events = fetch_events_logs_with_retry(
                            "Withdraw using CT on pairs with USDe",
                            self.psm_contract.events.CtRedeemed(),
                            start,
                            to_block,
                            filter = {
                                "id": pair_id,
                                "dsId": term_id,
                            },
                        )

                        # event DsRedeemed(Id indexed id, uint256 indexed dsId, address indexed redeemer, uint256 paUsed, uint256 dsUsed, uint256 raReceived, uint256 dsExchangeRate, uint256 feePercentage, uint256 fee)
                        # IN: DS + PA
                        # OUT: RA
                        redeem_events = fetch_events_logs_with_retry(
                            "Redeem using DS on pairs with USDe",
                            self.psm_contract.events.DsRedeemed(),
                            start,
                            to_block,
                            filter = {
                                "id": pair_id,
                                "dsId": term_id,
                            },
                        )

                        # event Repurchased(Id indexed id, address indexed buyer, uint256 indexed dsId, uint256 raUsed, uint256 receivedPa, uint256 receivedDs, uint256 feePercentage, uint256 fee, uint256 exchangeRates)
                        # IN: RA
                        # OUT: PA + DS
                        repurchase_events = fetch_events_logs_with_retry(
                            "Repurchase on pairs with USDe",
                            self.psm_contract.events.Repurchased(),
                            start,
                            to_block,
                            filter = {
                                "id": pair_id,
                                "dsId": term_id,
                            },
                        )

                        # TODO: Rollover Events
                        if pair_config.eligible_asset == TokenType.RA:
                            balance_in = sum(
                                [event["args"]["amount"] for event in deposit_events] +
                                [event["args"]["raUsed"] for event in repurchase_events]
                            )
                            balance_out = sum(
                                [event["args"]["raReceived"] for event in withdraw_events] +
                                [event["args"]["raReceived"] for event in redeem_events]
                            )
                        elif pair_config.eligible_asset == TokenType.PA:
                            balance_in = sum(
                                [event["args"]["paUsed"] for event in redeem_events]
                            )
                            balance_out = sum(
                                [event["args"]["paReceived"] for event in withdraw_events] +
                                [event["args"]["receivedPa"] for event in repurchase_events]
                            )
                        else:
                            raise NotImplementedError("Token type not yet implemented")

                        # Update asset balance of share token
                        share_token_addr = term_config.share_token_addr
                        vault_bals.setdefault(share_token_addr, VaultBalance(0, 0))
                        vault_bals[share_token_addr].total_assets += balance_in - balance_out

                        # calls = [
                        #     (self.contract, self.contract_function.fn_name, [user_info.address])
                        #     for user_info in self.start_state
                        # ]
                        # results = multicall(self.w3, calls, block)
                        # multicall(self.w3, calls, block)

                # For each share token, accumulate all share-balance changes
                for share_token_addr, vault in vault_bals.items():
                    share_token_contract = self.w3.eth.contract(
                        address=share_token_addr,
                        abi=ERC20_ABI,
                    )

                    # event Transfer(address indexed from, address indexed to, uint256 value)
                    share_token_transfers = fetch_events_logs_with_retry(
                        "Token transfers of share token",
                        share_token_contract.events.Transfer(),
                        start,
                        to_block,
                    )

                    # Update share token balance of accounts involved in transfer
                    for transfer in share_token_transfers:
                        value = transfer["args"]["value"]

                        sender = Web3.to_checksum_address(transfer["args"]["from"])
                        if sender not in self.excluded_addresses:
                            vault.shares_by_account.setdefault(sender, 0)
                            vault.shares_by_account[sender] -= value
                        elif sender == ZERO_ADDRESS:
                            # token was minted, update total supply
                            vault.total_supply += value

                        recipient = Web3.to_checksum_address(transfer["args"]["to"])
                        if recipient not in self.excluded_addresses:
                            vault.shares_by_account.setdefault(recipient, 0)
                            vault.shares_by_account[recipient] += value
                        elif sender == ZERO_ADDRESS:
                            # token was minted, update total supply
                            vault.total_supply -= value

                start = to_block + 1
                # continue pagination

            # finished pagination loop, block height reached...
            # Calculate fractional balance of each account (share token holders)
            for vault in vault_bals.values():
                for account_addr, account_shares in vault.shares_by_account.items():
                    account_bals.setdefault(account_addr, 0)
                    account_bals[account_addr] += vault.total_assets * account_shares / vault.total_supply

            # Round off to 4 decimals
            for account_addr, account_bal in account_bals.items():
                account_bals[account_addr] = round((account_bal / 1e18), 4)

            new_block_data[block] = account_bals
            cache_copy_of_account_bals[block] = account_bals
        return new_block_data


if __name__ == "__main__":
    # simple tests for the integration
    cork_integration = CorkIntegration(
        integration_id=IntegrationID.CORK_USDE_CT,
        start_block=PSM_USDE_START_BLOCK_BY_CHAIN[Chain.SEPOLIA],
        summary_cols=[SummaryColumn.CORK_PSM_PTS],
        chain=Chain.SEPOLIA,
        reward_multiplier=50,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
            LV_ADDRESS_BY_CHAIN[Chain.SEPOLIA], # prevents Liquidity Vault from being counted
        },
    )

    print("=" * 120)
    print("Run without cached data",
        cork_integration.get_block_balances(
            cached_data={}, blocks=[20000000, 20000001, 20000002]
        )
    )
    # Example output:
    # {
    #   20000000: {"0x123": 100, "0x456": 200},
    #   20000001: {"0x123": 101, "0x456": 201},
    #   20000002: {"0x123": 102, "0x456": 202},
    # }

    print("=" * 120, "\n" * 5)
    print("Run with cached data",
        cork_integration.get_block_balances(
            cached_data={
                20000000: {
                    Web3.to_checksum_address("0x123"): 100,
                    Web3.to_checksum_address("0x456"): 200,
                },
                20000001: {
                    Web3.to_checksum_address("0x123"): 101,
                    Web3.to_checksum_address("0x456"): 201,
                },
            },
            blocks=[20000002],
        )
    )
    print("=" * 120)
    # Example output:
    # {
    #   20000002: {"0x123": 102, "0x456": 202},
    # }
