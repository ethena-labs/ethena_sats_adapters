from copy import deepcopy
import logging

from typing import Dict, List, Optional

from constants.midas import MIDAS_MWILDUSD_CONTRACT, MIDAS_MWILDUSD_START_BLOCK, PAGINATION_SIZE, ZERO_ADDRESS
from constants.summary_columns import SummaryColumn
from eth_typing import ChecksumAddress

from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.cached_balances_integration import CachedBalancesIntegration
from utils.web3_utils import fetch_events_logs_with_retry


class MidasIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            summary_cols,
            reward_multiplier,
        )

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block data for Midas")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to Midas get_block_balances")
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
            # parse transfer events since and update bals
            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)
                transfers = fetch_events_logs_with_retry(
                    "Token transfers Midas",
                    MIDAS_MWILDUSD_CONTRACT.events.Transfer(),
                    start,
                    to_block,
                )
                for transfer in transfers:
                    if transfer["args"]["from"] != ZERO_ADDRESS:
                        continue
                    user = transfer["args"]["to"]
                    if user not in bals:
                        bals[user] = 0
                    bals[user] += round(transfer["args"]["value"] / 10**18, 4)
                start = to_block + 1
            new_block_data[block] = bals
            cache_copy[block] = bals
        return new_block_data


if __name__ == "__main__":
    midas_integration = MidasIntegration(
        integration_id=IntegrationID.MIDAS_MWILDUSD,
        start_block=MIDAS_MWILDUSD_START_BLOCK,
        summary_cols=[SummaryColumn.MIDAS_MWILDUSD_PTS],
        reward_multiplier=20,
    )

    # Without cached data
    without_cached_data_output = midas_integration.get_block_balances(
        cached_data={}, blocks=[23441782,23441783]
    )

    print("=" * 120)
    print("Run without cached data", without_cached_data_output)
    print("=" * 120, "\n" * 5)

    # With cached data, using the previous output so there is no need
    # to fetch the previous blocks again
    with_cached_data_output = midas_integration.get_block_balances(
        cached_data=without_cached_data_output, blocks=[23441782,23441783]
    )
    print("Run with cached data", with_cached_data_output)
    print("=" * 120)
