from copy import deepcopy
import json
import logging
import os
from typing import Callable, Dict, List, Optional, Set
from web3 import Web3
from eth_typing import ChecksumAddress
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import w3, fetch_events_logs_with_retry


PAGINATION_SIZE = int(os.getenv("PAGINATION_SIZE", "1000"))

# 1w 2w 4w 6w 8w 13w
LIUSD_ADDRESSES = [
    Web3.to_checksum_address("0x12b004719fb632f1E7c010c6F5D6009Fb4258442"),
    Web3.to_checksum_address("0xf1839BeCaF586814D022F16cDb3504ff8D8Ff361"),
    Web3.to_checksum_address("0x66bCF6151D5558AfB47c38B20663589843156078"),
    Web3.to_checksum_address("0xb06Cc4548FebfF3D66a680F9c516381c79bC9707"),
    Web3.to_checksum_address("0xf68b95b7e851170c0e5123a3249dD1Ca46215085"),
    Web3.to_checksum_address("0xbd3f9814eB946E617f1d774A6762cDbec0bf087A")
]

with open("abi/ERC20_abi.json") as f:
    ERC20_ABI = json.load(f)

LIUSD_CONTRACTS = {}
for address in LIUSD_ADDRESSES:
    LIUSD_CONTRACTS[address] = w3.eth.contract(
        address=address,
        abi=ERC20_ABI,
    )

class InfiniFiIntegration (
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

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("[Infinifi liUSD integration] Getting block data...")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("[Infinifi liUSD integration] No blocks provided for infinifi liUSD get_block_balances")
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
                    logging.debug(f"[Infinifi liUSD integration] Found previous block {prev_block} with {len(bals)} balances to use as base for fetching balance at block {block}")
                    break
            # parse transfer events since and update bals
            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)
                # get transfers from all liUSD addresses and sum them up
                # exchange rate does not matter between all liUSD tokens
                # so we can just sum them up
                all_events = []
                for liusd_address in LIUSD_ADDRESSES:
                    logging.debug(f"[Infinifi liUSD integration]Fetching transfers from {start} to {to_block}")
                    transfers = fetch_events_logs_with_retry(
                        "liUSD token transfers",
                        LIUSD_CONTRACTS[liusd_address].events.Transfer(),
                        start,
                        to_block,
                    )
                    all_events.extend(transfers)
                for transfer in all_events:
                    sender = transfer["args"]["from"]
                    recipient = transfer["args"]["to"]
                    if sender not in bals:
                        bals[sender] = 0
                    if recipient not in bals:
                        bals[recipient] = 0

                    amount = round(transfer["args"]["value"] / 10**18, 4)
                    if recipient not in self.excluded_addresses:
                        bals[recipient] += amount
                    if sender not in self.excluded_addresses:
                        bals[sender] -= amount
                    
                    # remove 0 or negative balances
                    # negative balances are possible due to rounding errors
                    if bals[sender] <= 0:
                        del bals[sender]
                    if bals[recipient] <= 0:
                        del bals[recipient]
                start = to_block + 1
            new_block_data[block] = bals
            cache_copy[block] = bals
        return new_block_data



if __name__ == "__main__":
    # TODO: Write simple tests for the integration
    example_integration = InfiniFiIntegration(
        integration_id=IntegrationID.INFINIFI_LIUSD,
        start_block=22540416, # liUSD deploy block
        summary_cols=[SummaryColumn.INFINIFI_LIUSD_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=40000000,
    )
    
    
    previous_balances =  example_integration.get_block_balances(
                cached_data={}, blocks=[22540500, 22541000, 22542000, 22645137]
            )
    
    # save output as json with proper line return
    with open("infinifi_liusd_balances.json", "w") as f:
        json.dump(previous_balances,f,indent=4)
        
    new_balances = example_integration.get_block_balances(
                cached_data=previous_balances, blocks=[22666601]
            )
    
    with open("infinifi_liusd_balances_2.json", "w") as f:
        json.dump(new_balances,f,indent=4)
