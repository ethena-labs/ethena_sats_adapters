import logging
from copy import deepcopy
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Callable, Dict, List, NewType, Optional, Set, NamedTuple

from web3 import Web3
from eth_typing import ChecksumAddress

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from constants.cork import (
    AMM_CONTRACT_BY_CHAIN,
    SUSDE_TOKEN_ADDRESS_BY_CHAIN,
    PSM_SUSDE_START_BLOCK_BY_CHAIN,
    PSM_CONTRACT_BY_CHAIN,
    LV_ADDRESS_BY_CHAIN,
    PAGINATION_SIZE,
    ZERO_ADDRESS,
    ERC20_ABI,
    TokenType,
)

from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import fetch_events_logs_with_retry, multicall, W3_BY_CHAIN

########################################################################
# Terminologies
########################################################################
# Cork PSM (PSM - Peg Stability Model/Module):
#   - Fixed-term PSMs with pools for peg stability between a pair of assets
# Cork AMM (AMM - Automated Market Maker):
#   - Fixed-term AMMs with pools to enable swaps between the tokens of each Cork Market
# Cork Vaults (LV - Liquidity Vault):
#   - Long-term Vaults that deploy liquidity into Cork PSM pools and Cork AMM pools

# Typings
TermId = NewType("TermId", int)
PsmShareTokenAddress = NewType("PsmShareTokenAddress", ChecksumAddress)
LpTokenAddress = NewType("LpTokenAddress", ChecksumAddress)
QuoteTokenAddress = NewType("QuoteTokenAddress", ChecksumAddress)
VaultShareTokenAddress = NewType("VaultShareTokenAddress", ChecksumAddress)

class TermConfig(NamedTuple):
    share_token_addr: PsmShareTokenAddress
    amm_lp_token_addr: LpTokenAddress
    amm_pool_addr: ChecksumAddress
    start_block: int

class PairConfig(NamedTuple):
    eligible_asset: TokenType
    amm_quote_token_addr: QuoteTokenAddress
    vault_share_token_addr: VaultShareTokenAddress
    vault_addr: ChecksumAddress
    start_block: int
    terms: Dict[TermId, TermConfig]

@dataclass
class PooledBalance:
    '''
    PooledBalance is a class that represents the balances of a pool or ERC4626 vault.
        It contains the following attributes:
        - total_assets: the total amount of the eligible asset in the pool
        - total_assets_by_token: a dictionary of the total amount of the other assets in the pool
        - total_supply: the total supply of the shares
        - shares_by_account: a dictionary that maps each account address to its share of the pool
    '''
    pair_config: PairConfig
    term_config: Optional[TermConfig] = None
    total_assets: int = 0
    # total_assets_by_token: Dict[ChecksumAddress, int | Decimal] = {}
    total_supply: int = 0
    shares_by_account: Dict[ChecksumAddress, int] = field(default_factory=dict)


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
        self.eligible_token_addr = SUSDE_TOKEN_ADDRESS_BY_CHAIN[self.chain]

        self.pair_config_by_id: Dict[bytes, PairConfig] = None
        self.psm_contract = PSM_CONTRACT_BY_CHAIN[self.chain]
        self.psm_balances_by_share_token: Dict[PsmShareTokenAddress, PooledBalance] = None

        self.amm_contract = AMM_CONTRACT_BY_CHAIN[self.chain]
        self.amm_balances_by_lp_token: Dict[LpTokenAddress, PooledBalance] = None

        self.vault_balances_by_vault_share_token: Dict[VaultShareTokenAddress, PooledBalance] = None


    def update_pair_config(
        self,
        pair_config_by_id: Dict[bytes, PairConfig],
        from_block: int = 0,
        to_block: int | str = "latest"
    ) -> Dict[bytes, PairConfig]:
        # Fetch events that indicates new pair was created
        new_pair_events_with_eligible_pa = fetch_events_logs_with_retry(
            "Pairs initialized with USDe as PA",
            self.psm_contract.events.InitializedModuleCore(),
            from_block or self.start_block,
            to_block,
            filter = {
                "pa": self.eligible_token_addr,
            },
        )
        new_pair_events_with_eligible_ra = fetch_events_logs_with_retry(
            "Pairs initialized with USDe as RA",
            self.psm_contract.events.InitializedModuleCore(),
            from_block or self.start_block,
            to_block,
            filter = {
                "ra": self.eligible_token_addr,
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

        # Set new pairs to config
        pair_config_by_id.update({
            event["args"]["id"]: PairConfig(
                eligible_asset=TokenType.PA,
                amm_quote_token_addr=Web3.to_checksum_address(event["args"]["ra"]),
                vault_share_token_addr=Web3.to_checksum_address(event["args"]["lv"]),
                vault_addr=LV_ADDRESS_BY_CHAIN[self.chain],
                start_block=event["blockNumber"],
                terms={},
            )
            for event in new_pair_events_with_eligible_pa
            # if event["args"]["pa"] == self.eligible_token_addr
        } | {
            event["args"]["id"]: PairConfig(
                eligible_asset=TokenType.RA,
                amm_quote_token_addr=Web3.to_checksum_address(event["args"]["ra"]),
                vault_share_token_addr=Web3.to_checksum_address(event["args"]["lv"]),
                vault_addr=LV_ADDRESS_BY_CHAIN[self.chain],
                start_block=event["blockNumber"],
                terms={},
            )
            for event in new_pair_events_with_eligible_ra
            # if event["args"]["ra"] == self.eligible_token_addr
        })

        # For each pair, update term config...
        for pair_id, pair_config in pair_config_by_id.items():
            # Fetch events that indicate a new term was issued/started
            new_term_events_of_pair = fetch_events_logs_with_retry(
                "Issuance on pairs with USDe",
                self.psm_contract.events.Issued(),
                pair_config.start_block or self.start_block,
                to_block,
                filter = {
                    "id": pair_id,
                },
            )

            # Get LP token address
            # WORKAROUND: until LP token address is available from Issued event
            amm_contract_function = self.amm_contract.functions.getLiquidityToken
            amm_calls = [
                (
                    self.amm_contract,
                    amm_contract_function.fn_name,
                    [pair_config.amm_quote_token_addr, event["args"]["ct"]],
                )
                for event in new_term_events_of_pair
            ]
            multicall_results = multicall(self.w3, amm_calls, to_block)
            for event, result in zip(new_term_events_of_pair, multicall_results):
                event["args"]["lpt"] = result[0]

            # For each term, update config...
            for event in new_term_events_of_pair:
                # pylint: disable=line-too-long
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
                # pylint: enable=line-too-long

                # the `ds_id` identifies each term, but is not unique globally (across pairs)
                term_id: TermId = TermId(event["args"]["dsId"])

                # the `share_token_addr` is unique and only valid for each term (or issuance)
                # the `lp_token_addr` is also unique and only valid for each term (or issuance)
                term_config = TermConfig(
                    share_token_addr=Web3.to_checksum_address(event["args"]["ct"]),
                    amm_lp_token_addr=Web3.to_checksum_address(event["args"]["lpt"]),
                    amm_pool_addr=self.amm_contract.address,
                    start_block=event["blockNumber"],
                )

                # Add new term to config
                pair_config.terms[term_id] = term_config
        return pair_config_by_id


    def update_psm_pool_balances(
        self,
        pool_balances: Dict[PsmShareTokenAddress, PooledBalance],
        from_block: int = 0,
        to_block: int | str = "latest"
    ) -> Dict[PsmShareTokenAddress, PooledBalance]:
        # For each pair...
        for pair_id, pair_config in self.pair_config_by_id.items():
            # For each term, accumulate all changes on amount of assets locked in PSM...
            for term_id, term_config in pair_config.terms.items():
                start_block = max(from_block, term_config.start_block)

                # Fetch various events when assets are going IN or OUT of the PSM pool:
                # pylint: disable=line-too-long

                # event PsmDeposited(Id indexed id, uint256 indexed dsId, address indexed depositor, uint256 amount, uint256 received, uint256 exchangeRate)
                # IN: RA
                # OUT: DS + CT
                deposit_events = fetch_events_logs_with_retry(
                    "Deposit on pairs with USDe",
                    self.psm_contract.events.PsmDeposited(),
                    start_block,
                    to_block,
                    filter = {
                        "id": pair_id,
                        "dsId": int(term_id),
                    },
                )

                # event CtRedeemed(Id indexed id, uint256 indexed dsId, address indexed redeemer, uint256 amount, uint256 paReceived, uint256 raReceived)
                # IN: CT
                # OUT: PA + RA
                withdraw_events = fetch_events_logs_with_retry(
                    "Withdraw using CT on pairs with USDe",
                    self.psm_contract.events.CtRedeemed(),
                    start_block,
                    to_block,
                    filter = {
                        "id": pair_id,
                        "dsId": int(term_id),
                    },
                )

                # event DsRedeemed(Id indexed id, uint256 indexed dsId, address indexed redeemer, uint256 paUsed, uint256 dsUsed, uint256 raReceived, uint256 dsExchangeRate, uint256 feePercentage, uint256 fee)
                # IN: DS + PA
                # OUT: RA
                redeem_events = fetch_events_logs_with_retry(
                    "Redeem using DS on pairs with USDe",
                    self.psm_contract.events.DsRedeemed(),
                    start_block,
                    to_block,
                    filter = {
                        "id": pair_id,
                        "dsId": int(term_id),
                    },
                )

                # event Repurchased(Id indexed id, address indexed buyer, uint256 indexed dsId, uint256 raUsed, uint256 receivedPa, uint256 receivedDs, uint256 feePercentage, uint256 fee, uint256 exchangeRates)
                # IN: RA
                # OUT: PA + DS
                repurchase_events = fetch_events_logs_with_retry(
                    "Repurchase on pairs with USDe",
                    self.psm_contract.events.Repurchased(),
                    start_block,
                    to_block,
                    filter = {
                        "id": pair_id,
                        "dsId": int(term_id),
                    },
                )
                # pylint: enable=line-too-long

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

                # Get pooled balances of each PSM
                share_token_addr = term_config.share_token_addr
                pool_balances.setdefault(share_token_addr, PooledBalance(pair_config, term_config))
                pool = pool_balances[share_token_addr]

                # Update asset balance of PSM pool
                pool.total_assets += balance_in - balance_out

                # For each token, accumulate all balance changes from Transfer events...
                token_contract = self.w3.eth.contract(
                    address=share_token_addr,
                    abi=ERC20_ABI,
                )

                # event Transfer(address indexed from, address indexed to, uint256 value)
                token_transfers = fetch_events_logs_with_retry(
                    "Token transfers of PSM CT token",
                    token_contract.events.Transfer(),
                    start_block,
                    to_block,
                )

                # Update token balance of accounts involved in transfer
                for transfer in token_transfers:
                    value = int(transfer["args"]["value"])

                    sender = Web3.to_checksum_address(transfer["args"]["from"])
                    if sender not in self.excluded_addresses:
                        pool.shares_by_account.setdefault(sender, 0)
                        pool.shares_by_account[sender] -= value
                    elif sender == ZERO_ADDRESS:
                        # token was minted, update total supply
                        pool.total_supply += value

                    recipient = Web3.to_checksum_address(transfer["args"]["to"])
                    if recipient not in self.excluded_addresses:
                        pool.shares_by_account.setdefault(recipient, 0)
                        pool.shares_by_account[recipient] += value
                    elif sender == ZERO_ADDRESS:
                        # token was burned, update total supply
                        pool.total_supply -= value
        return pool_balances


    def update_amm_pool_balances(
        self,
        pool_balances: Dict[LpTokenAddress, PooledBalance],
        from_block: int = 0,
        to_block: int | str = "latest"
    ) -> Dict[LpTokenAddress, PooledBalance]:
        # For each pair...
        for _pair_id, pair_config in self.pair_config_by_id.items():
            # For each term...
            for _term_id, term_config in pair_config.terms.items():
                start_block = max(from_block, term_config.start_block)

                # Get pooled balances of each AMM pair
                lp_token_addr = term_config.amm_lp_token_addr
                pool_balances.setdefault(lp_token_addr, PooledBalance(pair_config, term_config))
                pool = pool_balances[lp_token_addr]

                # For each token, accumulate all balance changes from Transfer events...
                token_contract = self.w3.eth.contract(
                    address=lp_token_addr,
                    abi=ERC20_ABI,
                )

                # event Transfer(address indexed from, address indexed to, uint256 value)
                token_transfers = fetch_events_logs_with_retry(
                    "Token transfers of AMM LP token",
                    token_contract.events.Transfer(),
                    start_block,
                    to_block,
                )

                # Update token balance of accounts involved in transfer
                for transfer in token_transfers:
                    value = int(transfer["args"]["value"])

                    sender = Web3.to_checksum_address(transfer["args"]["from"])
                    if sender not in self.excluded_addresses:
                        pool.shares_by_account.setdefault(sender, 0)
                        pool.shares_by_account[sender] -= value
                    elif sender == ZERO_ADDRESS:
                        # token was minted, update total supply
                        pool.total_supply += value

                    recipient = Web3.to_checksum_address(transfer["args"]["to"])
                    if recipient not in self.excluded_addresses:
                        pool.shares_by_account.setdefault(recipient, 0)
                        pool.shares_by_account[recipient] += value
                    elif sender == ZERO_ADDRESS:
                        # token was burned, update total supply
                        pool.total_supply -= value
        return pool_balances


    def update_vault_pool_balances(
        self,
        pool_balances: Dict[VaultShareTokenAddress, PooledBalance],
        from_block: int = 0,
        to_block: int | str = "latest"
    ) -> Dict[VaultShareTokenAddress, PooledBalance]:
        # For each pair...
        for _pair_id, pair_config in self.pair_config_by_id.items():
            start_block = max(from_block, pair_config.start_block)

            vault_share_token_addr = pair_config.vault_share_token_addr
            pool_balances.setdefault(vault_share_token_addr, PooledBalance(pair_config))
            pool = pool_balances[pool_balances]

            # For each token, accumulate all balance changes from Transfer events...
            token_contract = self.w3.eth.contract(
                address=vault_share_token_addr,
                abi=ERC20_ABI,
            )

            # event Transfer(address indexed from, address indexed to, uint256 value)
            token_transfers = fetch_events_logs_with_retry(
                "Token transfers of Vault LV token",
                token_contract.events.Transfer(),
                start_block,
                to_block,
            )

            # Update token balance of accounts involved in transfer
            for transfer in token_transfers:
                value = int(transfer["args"]["value"])

                sender = Web3.to_checksum_address(transfer["args"]["from"])
                if sender not in self.excluded_addresses:
                    pool.shares_by_account.setdefault(sender, 0)
                    pool.shares_by_account[sender] -= value
                elif sender == ZERO_ADDRESS:
                    # token was minted, update total supply
                    pool.total_supply += value

                recipient = Web3.to_checksum_address(transfer["args"]["to"])
                if recipient not in self.excluded_addresses:
                    pool.shares_by_account.setdefault(recipient, 0)
                    pool.shares_by_account[recipient] += value
                elif sender == ZERO_ADDRESS:
                    # token was burned, update total supply
                    pool.total_supply -= value
        return pool_balances


    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        # pylint: disable=line-too-long
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
        # pylint: enable=line-too-long
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
            account_bals: Dict[ChecksumAddress, Decimal | float] = {}

            for existing_block in sorted_existing_blocks:
                if existing_block < block:
                    prev_block = existing_block
                    start = existing_block + 1
                    account_bals = deepcopy(cache_copy_of_account_bals[prev_block])
                    break

            # Fetch pair config at prev_block if not already done
            if self.pair_config_by_id is None:
                self.pair_config_by_id = self.update_pair_config({}, to_block=prev_block)

            # Fetch Peg Stability term balances at prev_block if not already done
            if self.psm_balances_by_share_token is None:
                self.psm_balances_by_share_token = self.update_psm_pool_balances(
                    {}, to_block=prev_block)

            # Fetch AMM Liquidity Pool term balances at prev_block if not already done
            if self.amm_balances_by_lp_token is None:
                self.amm_balances_by_lp_token = self.update_amm_pool_balances(
                    {}, to_block=prev_block)

            # Fetch Vault term balances at prev_block if not already done
            if self.vault_balances_by_vault_share_token is None:
                self.vault_balances_by_vault_share_token = self.update_vault_pool_balances(
                    {}, to_block=prev_block)

            # parse events since and update bals
            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)
                # print(f"Fetching events from {start} to {to_block}")

                # Add new pairs to config
                self.update_pair_config(self.pair_config_by_id, start, to_block)

                # Update PSM Pool term balances
                self.update_psm_pool_balances(self.psm_balances_by_share_token, start, to_block)

                # Update AMM Pool term balances
                self.update_amm_pool_balances(self.amm_balances_by_lp_token, start, to_block)

                # Update Vault Liquidity Pool term balances
                self.update_vault_pool_balances(
                    self.vault_balances_by_vault_share_token,
                    start,
                    to_block
                )

                start = to_block + 1
                # continue pagination

            # finished pagination loop, block height reached...
            # Filter out non-eligible AMM pools
            eligible_amm_balances = {
                lp_token_addr: amm_pool
                for lp_token_addr, amm_pool in self.amm_balances_by_lp_token.items()
                if amm_pool.pair_config.amm_quote_token_addr == self.eligible_token_addr
            }

            # Fetch the reserve asset balances of each eligible AMM pool
            # Note: We cannot assume that all LP token holders have withdrawn
            # remaining reserves after end of epoch/term.
            amm_contract_function = self.amm_contract.functions.getReserves
            amm_calls = [
                (
                    self.amm_contract,
                    amm_contract_function.fn_name,
                    [
                        amm_pool.pair_config.amm_quote_token_addr,
                        amm_pool.term_config.share_token_addr
                    ],
                )
                for amm_pool in eligible_amm_balances.values()
            ]
            multicall_results = multicall(self.w3, amm_calls, block)

            # The results contain the following:
            #   - The `result[0]` is the total balance of the asset token in the AMM pool
            #   - The `result[1]` is the total balance of the share token in the AMM pool
            for amm_pool, result in zip(eligible_amm_balances.values(), multicall_results):
                # Update the total asset balance of each AMM pool
                amm_pool.total_assets = result[0]

                # Update the total shares of PSM pool of each AMM pool
                # amm_pool.total_assets_by_token[amm_pool.term_config.share_token_addr] = result[1]

            # Attribute Ethena asset balances on AMM pools to their respective LP token holders
            for amm_pool in self.amm_balances_by_lp_token.values():
                for account_addr, account_shares in amm_pool.shares_by_account.items():
                    amount = (
                        Decimal(amm_pool.total_assets)
                        * Decimal(account_shares)
                        / Decimal(amm_pool.total_supply)
                    )
                    # If the account_addr is the vault_addr, then we need to attribute the
                    # Ethena asset balances to the respective LV token holders
                    if account_addr == amm_pool.pair_config.vault_addr:
                        vault_share_token_addr = amm_pool.pair_config.vault_share_token_addr
                        vault = self.vault_balances_by_vault_share_token[vault_share_token_addr]
                        for account_addr, account_shares in vault.shares_by_account.items():
                            account_bals.setdefault(account_addr, Decimal(0))
                            account_bals[account_addr] = Decimal(account_bals[account_addr]) + (
                                amount
                                * Decimal(account_shares)
                                / Decimal(vault.total_supply)
                            )
                    else:
                        account_bals.setdefault(account_addr, Decimal(0))
                        account_bals[account_addr] = Decimal(account_bals[account_addr]) + amount

                    # # Attribute PSM share token balances to their respective LP token holders
                    # if amm_pool.term_config is not None:
                    #     share_token_addr = amm_pool.term_config.share_token_addr
                    #     psm_pool = self.psm_balances_by_share_token[share_token_addr]
                    #     account_share_token_bals = psm_pool.shares_by_account
                    #     share_amount = (
                    #         Decimal(amm_pool.total_assets_by_token[share_token_addr])
                    #         * Decimal(account_shares)
                    #         / Decimal(amm_pool.total_supply)
                    #     )
                    #     account_share_token_bals.setdefault(account_addr, Decimal(0))
                    #     bal = Decimal(account_share_token_bals[account_addr])
                    #     account_share_token_bals[account_addr] = bal + share_amount

            # Attribute Ethena asset balances on PSM pools to their respective CT token holders
            for psm_pool in self.psm_balances_by_share_token.values():
                for account_addr, account_shares in psm_pool.shares_by_account.items():
                    amount = (
                        Decimal(psm_pool.total_assets)
                        * Decimal(account_shares)
                        / Decimal(psm_pool.total_supply)
                    )
                    # If the account_addr is the vault_addr, then we need to attribute the
                    # Ethena asset balances to the respective LV token holders
                    if account_addr == psm_pool.pair_config.vault_addr:
                        vault_share_token_addr = psm_pool.pair_config.vault_share_token_addr
                        vault = self.vault_balances_by_vault_share_token[vault_share_token_addr]
                        for account_addr, account_shares in vault.shares_by_account.items():
                            account_bals.setdefault(account_addr, Decimal(0))
                            account_bals[account_addr] = Decimal(account_bals[account_addr]) + (
                                amount
                                * Decimal(account_shares)
                                / Decimal(vault.total_supply)
                            )
                    # If the account_addr is the amm_contract, then we need to attribute the
                    # Ethena asset balances to the respective LP token holders
                    elif account_addr == psm_pool.term_config.amm_pool_addr:
                        lp_token_addr = psm_pool.term_config.amm_lp_token_addr
                        amm_pool = self.amm_balances_by_lp_token[lp_token_addr]
                        for account_addr, account_shares in amm_pool.shares_by_account.items():
                            account_bals.setdefault(account_addr, Decimal(0))
                            account_bals[account_addr] = Decimal(account_bals[account_addr]) + (
                                amount
                                * Decimal(account_shares)
                                / Decimal(amm_pool.total_supply)
                            )
                    else:
                        account_bals.setdefault(account_addr, Decimal(0))
                        account_bals[account_addr] = Decimal(account_bals[account_addr]) + amount

            # Round off to 4 decimals
            for account_addr, account_bal in account_bals.items():
                account_bals[account_addr] = round(account_bal / Decimal(1e18), 4)

            new_block_data[block] = account_bals
            cache_copy_of_account_bals[block] = account_bals
        return new_block_data


if __name__ == "__main__":
    # simple tests for the integration
    cork_integration = CorkIntegration(
        integration_id=IntegrationID.CORK_SUSDE,
        start_block=PSM_SUSDE_START_BLOCK_BY_CHAIN[Chain.ETHEREUM],
        summary_cols=[SummaryColumn.CORK_PSM_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=50,
        excluded_addresses={
            ZERO_ADDRESS,
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
