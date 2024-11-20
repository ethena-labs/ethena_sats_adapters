from copy import deepcopy
import logging

from typing import Dict, List, Optional

from constants.summary_columns import SummaryColumn
from eth_typing import ChecksumAddress

from constants.example_integrations import (
    ACTIVE_ENA_START_BLOCK_EXAMPLE,
    ENA_CONTRACT,
    PAGINATION_SIZE,
)

from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.cached_balances_integration import CachedBalancesIntegration
from utils.web3_utils import fetch_events_logs_with_retry


class ClaimedEnaIntegration(CachedBalancesIntegration):
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
        logging.info("Getting block data for claimed ENA")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to claimed ENA get_block_balances")
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
                # print(f"Fetching transfers from {start} to {to_block}")
                transfers = fetch_events_logs_with_retry(
                    "Token transfers claimed ENA",
                    ENA_CONTRACT.events.Transfer(),
                    start,
                    to_block,
                )
                for transfer in transfers:
                    recipient = transfer["args"]["to"]
                    if recipient not in bals:
                        bals[recipient] = 0
                    bals[recipient] += round(transfer["args"]["value"] / 10**18, 4)
                start = to_block + 1
            new_block_data[block] = bals
            cache_copy[block] = bals
        return new_block_data


if __name__ == "__main__":
    example_integration = ClaimedEnaIntegration(
        integration_id=IntegrationID.CLAIMED_ENA_EXAMPLE,
        start_block=ACTIVE_ENA_START_BLOCK_EXAMPLE,
        summary_cols=[SummaryColumn.CLAIMED_ENA_PTS_EXAMPLE],
        reward_multiplier=20,
    )

    # Without cached data
    without_cached_data_output = example_integration.get_block_balances(
        cached_data={}, blocks=[21209856, 21217056]
    )

    print("=" * 120)
    print("Run without cached data", without_cached_data_output)
    print("=" * 120, "\n" * 5)

    # With cached data, using the previous output so there is no need
    # to fetch the previous blocks again
    with_cached_data_output = example_integration.get_block_balances(
        cached_data=without_cached_data_output, blocks=[21224256]
    )
    print("Run with cached data", with_cached_data_output)
    print("=" * 120)
