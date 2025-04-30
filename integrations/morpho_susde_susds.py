from copy import deepcopy
import logging

from typing import Dict, List
from eth_typing import ChecksumAddress
from constants.chains import Chain
from constants.morpho_susde_susds import (
    MORPHO_CONTRACT,
    MORPHO_MARKET_IDS,
    MORPHO_SUSDE_SUSDS_START_BLOCK,
    PAGINATION_SIZE,
)
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID as IntID
from utils.web3_utils import fetch_events_logs_with_retry


class MorphoSusdeSusds(CachedBalancesIntegration):
    """
    Morpho sUSDe-sUSDS LP token market integration.
    """

    def __init__(self):
        super().__init__(
            integration_id=IntID.MORPHO_SUSDE_SUSDS,
            start_block=MORPHO_SUSDE_SUSDS_START_BLOCK,
            chain=Chain.ETHEREUM,
            summary_cols=[SummaryColumn.MORPHO_SUSDE_SUSDS_PTS],
            reward_multiplier=5,
            balance_multiplier=1,
        )

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block data for Morpho sUSDe-sUSDS LP collateral")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error(
                "No blocks provided to Morpho sUSDe-sUSDS LP collateral get_block_balances"
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
            # parse supply/withdraw events since and update bals
            # NOTE: as per the morpho-blue EventsLib.sol comments,
            # `feeRecipient` receives supplied shares without any event,
            # so their sats are not accrued.
            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)

                supplies = fetch_events_logs_with_retry(
                    "Morpho-Borrow Supply with sUSDe",
                    MORPHO_CONTRACT.events.SupplyCollateral(),
                    start,
                    to_block,
                    filter={"id": MORPHO_MARKET_IDS},
                )
                for supply in supplies:
                    recipient = supply["args"]["onBehalf"]
                    if recipient not in bals:
                        bals[recipient] = 0
                    bals[recipient] += round(supply["args"]["assets"] / 10**18, 4)

                withdraws = fetch_events_logs_with_retry(
                    "Morpho-Borrow Supply with sUSDe",
                    MORPHO_CONTRACT.events.WithdrawCollateral(),
                    start,
                    to_block,
                    filter={"id": MORPHO_MARKET_IDS},
                )
                for withdraw in withdraws:
                    recipient = withdraw["args"]["onBehalf"]
                    if recipient not in bals:
                        bals[recipient] = 0
                    bals[recipient] -= round(withdraw["args"]["assets"] / 10**18, 4)
                    if bals[recipient] < 0:
                        bals[recipient] = 0
                start = to_block + 1
            new_block_data[block] = bals
            cache_copy[block] = bals
        return new_block_data


if __name__ == "__main__":
    integration = MorphoSusdeSusds()

    # Without cached data
    without_cached_data_output = integration.get_block_balances(
        cached_data={}, blocks=[22429010, 22509414]
    )

    print("=" * 120)
    print("Run without cached data", without_cached_data_output)
    print("=" * 120, "\n" * 5)

    # With cached data, using the previous output so there is no need
    # to fetch the previous blocks again
    with_cached_data_output = integration.get_block_balances(
        cached_data=without_cached_data_output, blocks=[22529414]
    )
    print("Run with cached data", with_cached_data_output)
    print("=" * 120)
