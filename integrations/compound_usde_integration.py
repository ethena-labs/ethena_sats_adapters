import json
import logging
from copy import deepcopy
from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.example_integrations import PAGINATION_SIZE
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress
from utils.web3_utils import w3_mantle

from utils.web3_utils import fetch_events_logs_with_retry

COMPOUND_USDE_ADDRESS = Web3.to_checksum_address("0x606174f62cd968d8e684c645080fa694c1D7786E")
with open("abi/ERC20_abi.json") as f:
    ERC4626_ABI = json.load(f)

COMPOUND_USDE_CONTRACT = w3_mantle.eth.contract(
    address=COMPOUND_USDE_ADDRESS,
    abi=ERC4626_ABI,
)

ZERO_ADDRESS = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")


class CompoundUSDeIntegration(CachedBalancesIntegration):
    def __init__(
            self,
            integration_id: IntegrationID,
            start_block: int,
            chain: Chain = Chain.MANTLE,
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
        logging.info("Getting block data for claimed USDe")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to claimed USDe get_block_balances")
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
                    "Token transfers claimed USDe",
                    COMPOUND_USDE_CONTRACT.events.Transfer(),
                    start,
                    to_block,
                )
                for transfer in transfers:
                    recipient = transfer["args"]["to"]
                    if recipient not in bals:
                        bals[recipient] = 0
                    bals[recipient] += round(transfer["args"]["value"] / 10 ** 18, 4)
                start = to_block + 1
            new_block_data[block] = bals
            cache_copy[block] = bals
        return new_block_data


if __name__ == "__main__":
    example_integration = CompoundUSDeIntegration(
        integration_id=IntegrationID.COMPOUND_USDE,
        start_block=70789050,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        chain=Chain.MANTLE,
        reward_multiplier=20,
        excluded_addresses={
            ZERO_ADDRESS, COMPOUND_USDE_ADDRESS
        },
        end_block=90000000,
    )
    print(
        example_integration.get_block_balances(
            cached_data={}, blocks=[73060203]
        )
    )
