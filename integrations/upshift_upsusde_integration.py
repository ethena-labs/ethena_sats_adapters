import json
import logging
from copy import deepcopy
from typing import Callable, Dict, List, Optional, Set

from eth_typing import ChecksumAddress
from web3 import Web3
from utils.web3_utils import w3

from constants.chains import Chain
from constants.example_integrations import PAGINATION_SIZE
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import fetch_events_logs_with_retry

UPSUSDE_ADDRESS = Web3.to_checksum_address("0xd684AF965b1c17D628ee0d77cae94259c41260F4")
with open("abi/ERC4626_abi.json") as f:
    ERC4626_ABI = json.load(f)

UPSUSDE_CONTRACT = w3.eth.contract(
    address=UPSUSDE_ADDRESS,
    abi=ERC4626_ABI,
)
ZERO_ADDRESS = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")


class UpshiftupsUSDeIntegration(CachedBalancesIntegration):
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

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block data for upSUSDe")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to get_block_balances")
            return new_block_data
        sorted_blocks = sorted(blocks)
        cache_copy: Dict[int, Dict[ChecksumAddress, float]] = deepcopy(cached_data)
        for block in sorted_blocks:
            total_supply = UPSUSDE_CONTRACT.functions.totalSupply().call(
                block_identifier=block
            )
            total_assets = UPSUSDE_CONTRACT.functions.totalAssets().call(
                block_identifier=block
            )

            # convert balance of upsUSDe to implied sUSDe for this block
            assets_per_share = total_assets / total_supply if total_supply != 0 else 0

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
                    "Token transfers upsUSDe",
                    UPSUSDE_CONTRACT.events.Transfer(),
                    start,
                    to_block,
                )
                for transfer in transfers:
                    recipient = transfer["args"]["to"]
                    sender = transfer["args"]["from"]
                    value = transfer["args"]["value"] / 10**18
                    if recipient not in bals:
                        bals[recipient] = 0
                    if sender not in bals:
                        bals[sender] = 0
                    bals[recipient] += round(value, 4)
                    bals[sender] -= round(value, 4)
                start = to_block + 1
            cache_copy[block] = bals

            converted_bals = {}
            for addr, bal in bals.items():
                converted_bals[addr] = max(bal * assets_per_share, 0)
            new_block_data[block] = converted_bals

        return new_block_data


if __name__ == "__main__":
    example_integration = UpshiftupsUSDeIntegration(
        integration_id=IntegrationID.UPSHIFT_UPSUSDE,
        start_block=21324190,  # contract deployment
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={ZERO_ADDRESS, UPSUSDE_ADDRESS},
        end_block=None,
    )
    print(
        example_integration.get_block_balances(
            cached_data={}, blocks=[21324292, 21324963]
        )
    )
