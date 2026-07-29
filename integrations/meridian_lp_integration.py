import json
import logging
from copy import deepcopy
from typing import Callable, Dict, List, Optional, Set

from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.meridian import (
    MERIDIAN_LP_VAULT_ADDRESS,
    MERIDIAN_LP_VAULT_CHAIN,
    MERIDIAN_LP_VAULT_START_BLOCK,
    PAGINATION_SIZE,
)
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import W3_BY_CHAIN, call_with_retry, fetch_events_logs_with_retry

with open("abi/meridian_vault.json") as f:
    MERIDIAN_VAULT_ABI = json.load(f)

w3_meridian = W3_BY_CHAIN[MERIDIAN_LP_VAULT_CHAIN]["w3"]
MERIDIAN_VAULT_CONTRACT = w3_meridian.eth.contract(
    address=MERIDIAN_LP_VAULT_ADDRESS,
    abi=MERIDIAN_VAULT_ABI,
)
ZERO_ADDRESS = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")


class MeridianLiquidityProviderIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = MERIDIAN_LP_VAULT_CHAIN,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 30,
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
        self._share_unit: Optional[int] = None
        self._pps_cache: Dict[int, float] = {}

    def get_share_unit(self) -> int:
        # share decimals match the underlying asset decimals
        if self._share_unit is None:
            self._share_unit = 10 ** call_with_retry(
                MERIDIAN_VAULT_CONTRACT.functions.decimals()
            )
        return self._share_unit

    def get_pps(self, block: int) -> float:
        """
        Calculate price per share (in the underlying asset) for a given block and cache result.

        The vault's NAV lives in the strategy - totalAssets only reflects liquid assets held
        in the vault - so pricing must use convertToAssets (equal to sharePrice / 1e36) and
        not totalAssets / totalSupply.
        """
        if block in self._pps_cache:
            return self._pps_cache[block]

        share_unit = self.get_share_unit()
        pps = (
            call_with_retry(
                MERIDIAN_VAULT_CONTRACT.functions.convertToAssets(share_unit), block
            )
            / share_unit
        )
        self._pps_cache[block] = pps
        return pps

    def get_balance(self, user: str, block: int) -> float:
        balance = call_with_retry(
            MERIDIAN_VAULT_CONTRACT.functions.balanceOf(Web3.to_checksum_address(user)),
            block,
        )
        return balance / self.get_share_unit() * self.get_pps(block)

    def convert_block_balances_to_assets(
        self, block_balances: Dict[ChecksumAddress, float], block: int
    ) -> Dict[ChecksumAddress, float]:
        """
        Convert vault shares to underlying asset balances for a given block.
        """
        pps = self.get_pps(block)
        return {addr: value * pps for addr, value in block_balances.items()}

    def convert_block_balances_to_shares(
        self, block_balances: Dict[ChecksumAddress, float], block: int
    ) -> Dict[ChecksumAddress, float]:
        """
        Convert underlying asset balances to vault shares for a given block.
        """
        pps = self.get_pps(block)
        return {addr: value / pps for addr, value in block_balances.items()}

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """
        Get user balances for specified blocks, using cached data when available.

        This method returns and caches the balances in the underlying asset. Whenever cached
        data is passed, we convert it to vault shares for that block and process new transfer
        events. Afterwards, the balances dictionary is converted back to asset balances.

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
        logging.info("Getting block data for Meridian Liquidity Provider")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to get_block_balances")
            return new_block_data

        blocks = sorted(blocks)

        cache_copy: Dict[int, Dict[ChecksumAddress, float]] = deepcopy(cached_data)
        # convert cached data to shares
        cache_copy = {
            block: self.convert_block_balances_to_shares(balances, block)
            for block, balances in cache_copy.items()
        }

        for block in blocks:
            if block < self.start_block:
                new_block_data[block] = {}
                continue
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
                transfers = fetch_events_logs_with_retry(
                    "Token transfers Meridian Liquidity Provider",
                    MERIDIAN_VAULT_CONTRACT.events.Transfer(),
                    start,
                    to_block,
                )
                for transfer in transfers:
                    sender = transfer["args"]["from"]
                    recipient = transfer["args"]["to"]
                    value = transfer["args"]["value"] / self.get_share_unit()
                    if recipient not in balances:
                        balances[recipient] = 0
                    if sender not in balances:
                        balances[sender] = 0
                    balances[recipient] += value
                    balances[sender] -= value
                start = to_block + 1

            balances.pop(ZERO_ADDRESS, None)
            # shares are transferred to the vault on requestRedeem, so dropping the vault's
            # balance stops accrual for shares pending redemption
            balances.pop(MERIDIAN_LP_VAULT_ADDRESS, None)
            cache_copy[block] = balances
            new_block_data[block] = self.convert_block_balances_to_assets(
                balances, block
            )
        return new_block_data


if __name__ == "__main__":
    example_integration = MeridianLiquidityProviderIntegration(
        integration_id=IntegrationID.MERIDIAN_LIQUIDITY_PROVIDER,
        start_block=MERIDIAN_LP_VAULT_START_BLOCK,
        summary_cols=[SummaryColumn.MERIDIAN_LIQUIDITY_PROVIDER_PTS],
        chain=MERIDIAN_LP_VAULT_CHAIN,
        excluded_addresses={ZERO_ADDRESS, MERIDIAN_LP_VAULT_ADDRESS},
    )

    BLOCK_1 = 22560000
    BLOCK_2 = 22566000

    # Without cached data
    without_cached_data_output = example_integration.get_block_balances(
        cached_data={}, blocks=[BLOCK_1]
    )
    print("Run without cached data", without_cached_data_output)

    # With cached data, using the previous output so there is no need
    # to fetch the previous blocks again
    with_cached_data_output = example_integration.get_block_balances(
        cached_data=without_cached_data_output, blocks=[BLOCK_2]
    )
    print("Run with cached data", with_cached_data_output)

    # Fetch balances in one go up to BLOCK_2 and check the balance for user is the same
    integration_1 = MeridianLiquidityProviderIntegration(
        integration_id=IntegrationID.MERIDIAN_LIQUIDITY_PROVIDER,
        start_block=MERIDIAN_LP_VAULT_START_BLOCK,
        summary_cols=[SummaryColumn.MERIDIAN_LIQUIDITY_PROVIDER_PTS],
        chain=MERIDIAN_LP_VAULT_CHAIN,
        excluded_addresses={ZERO_ADDRESS, MERIDIAN_LP_VAULT_ADDRESS},
    )
    balances = integration_1.get_block_balances(cached_data={}, blocks=[BLOCK_2])

    user = Web3.to_checksum_address("0x023AB75D0F141F66b37f77Da71868Efd9Db4f17f")
    print("One-Go-Fetch", balances[BLOCK_2][user])
    print("Cache-Fetch", with_cached_data_output[BLOCK_2][user])
    print("Balance-Fetch", integration_1.get_balance(user, block=BLOCK_2))
