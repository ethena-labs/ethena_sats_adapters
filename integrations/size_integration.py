from typing import Callable, Dict, List, Optional, Set
from copy import deepcopy
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import fetch_events_logs_with_retry
from web3 import Web3
from eth_typing import ChecksumAddress
import logging

from constants.size import (
    SZSUSDE_CONTRACT,
    SZSUSDE_START_BLOCK,
    PAGINATION_SIZE,
)

class SizeIntegration(
    CachedBalancesIntegration
):
    def __init__(
        self,
        integration_id: IntegrationID = IntegrationID.SIZE_ETHEREUM_SUSDE,
        start_block: int = SZSUSDE_START_BLOCK,
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
        logging.info("Getting block data for Size")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided")
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
            # parse transfer events since and update balances
            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)
                # print(f"Fetching transfers from {start} to {to_block}")
                transfers = fetch_events_logs_with_retry(
                    "szsUSDe Token transfers",
                    SZSUSDE_CONTRACT.events.Transfer(),
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
    example_integration = SizeIntegration()
    print(
        example_integration.get_block_balances(
            cached_data={}, blocks=[21688149]
        )
    )
    # Example output:
    # {21688149: {'0x52f5E8A5E68fafcAc57b56bf62b886424d008dfd': 1.5387}}