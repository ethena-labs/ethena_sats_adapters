from copy import deepcopy
import logging
from rich.console import Console

from typing import Dict, List
from eth_typing import ChecksumAddress
from constants.chains import Chain
from constants.silo_finance import (
    SILO_FINANCE_MARKETS,
    SILO_FINANCE_LP_USDE_START_BLOCK,
    PAGINATION_SIZE,
)
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID as IntID
from utils.web3_utils import fetch_events_logs_with_retry


class SiloFinance(CachedBalancesIntegration):
    """
    Silo Finance LP-eUSDe token markets integration.
    """

    def __init__(self):
        super().__init__(
            integration_id=IntID.SILO_FINANCE_LP_USDE,
            start_block=SILO_FINANCE_LP_USDE_START_BLOCK,
            chain=Chain.ETHEREUM,
            summary_cols=[SummaryColumn.SILO_FINANCE_LP_USDE_PTS],
            reward_multiplier=30,
            balance_multiplier=1,
        )

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block data for Silo Finance LP-eUSDe")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error(
                "No blocks provided to Silo Finance LP-eUSDe get_block_balances"
            )
            return new_block_data

        sorted_blocks = sorted(blocks)
        cache_copy: Dict[int, Dict[ChecksumAddress, float]] = deepcopy(cached_data)

        for block in sorted_blocks:
            # find the closest prev block in the data
            # list keys parsed as ints and in descending order
            sorted_existing_blocks = sorted(
                cache_copy,
                reverse=True,
            )
            # loop through the sorted blocks and find the closest previous block
            prev_block = self.start_block
            start = prev_block
            bals = {}
            for existing_block in sorted_existing_blocks:
                if existing_block < block:
                    prev_block = existing_block
                    start = existing_block + 1
                    bals = deepcopy(cache_copy[prev_block])
                    break

            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)
                
                # supplies = fetch_events_logs_with_retry(
                #     "Morpho-Borrow Supply with sUSDe",
                #     MORPHO_CONTRACT.events.SupplyCollateral(),
                #     start,
                #     to_block,
                #     filter={"id": MORPHO_MARKET_IDS},
                # )
                # for supply in supplies:
                #     recipient = supply["args"]["onBehalf"]
                #     if recipient not in bals:
                #         bals[recipient] = 0
                #     bals[recipient] += round(supply["args"]["assets"] / 10**18, 4)

                # withdraws = fetch_events_logs_with_retry(
                #     "Morpho-Borrow Supply with sUSDe",
                #     MORPHO_CONTRACT.events.WithdrawCollateral(),
                #     start,
                #     to_block,
                #     filter={"id": MORPHO_MARKET_IDS},
                # )
                # for withdraw in withdraws:
                #     recipient = withdraw["args"]["onBehalf"]
                #     if recipient not in bals:
                #         bals[recipient] = 0
                #     bals[recipient] -= round(withdraw["args"]["assets"] / 10**18, 4)
                #     if bals[recipient] < 0:
                #         bals[recipient] = 0
                start = to_block + 1
                print(start, to_block)
            new_block_data[block] = bals
            cache_copy[block] = bals
        return new_block_data


if __name__ == "__main__":
    console = Console()

    integration = SiloFinance()

    # Without cached data
    without_cached_data_output = integration.get_block_balances(
        cached_data={}, blocks=[22693183, 22695554 + 1]
    )

    console.print("=" * 120)
    console.print("Run without cached data", without_cached_data_output)
    console.print("=" * 120, "\n" * 5)

    # With cached data, using the previous output so there is no need
    # to fetch the previous blocks again
    with_cached_data_output = integration.get_block_balances(
        cached_data=without_cached_data_output,
        blocks=[22693183 + 1000, 22693183 + 2000, 22693183 + 3000],
    )
    console.print("Run with cached data", with_cached_data_output)
    console.print("=" * 120)
