import json
import logging
from copy import deepcopy
from typing import Callable, Dict, List, Optional, Set, Tuple

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract import Contract
from web3.constants import ADDRESS_ZERO

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from constants.terminal import PRE_DEPOSIT_START_BLOCK, TUSDE_ADDRESS, PAGINATION_SIZE
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import fetch_events_logs_with_retry, w3
from utils.terminal import convert_to_decimals

with open("abi/ERC20_abi.json") as f:
    ERC20_ABI = json.load(f)

class TerminalIntegration(
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

    def find_closest_cached_data(
        self, block: int, cached_data: Dict[int, Dict[ChecksumAddress, float]]
    ) -> Tuple[int, Dict[ChecksumAddress, float]]:
        """
        Find the closest previous block in cached data to the given block.
        """
        if not cached_data:
            return PRE_DEPOSIT_START_BLOCK, {}

        latest_cached_block = max(cached_data.keys())
        if latest_cached_block >= block:
            logging.error("Requested block is not newer than cached data")
            return PRE_DEPOSIT_START_BLOCK, {}

        return latest_cached_block, deepcopy(cached_data[latest_cached_block])

    def fetch_transfers(
        self, tusde: Contract, from_block: int, to_block: int
    ):
        return fetch_events_logs_with_retry(
            f"Terminal Finance tUSDe transfers",
            contract_event=tusde.events.Transfer,
            from_block=from_block,
            to_block=to_block,
        )

    def process_transfer(
        self,
        transfer: Dict,
        cached_balances: Dict[ChecksumAddress, float]
    ):
        sender = transfer["args"]["from"]
        receiver = transfer["args"]["to"]
        value = transfer["args"]["value"]

        if sender != ADDRESS_ZERO:
            cached_balances[sender] = cached_balances.get(sender) - convert_to_decimals(value)
            # If balance is negative, set it to 0 (possible due to rounding errors)
            if cached_balances[sender] < 0: cached_balances[sender] = 0

        if receiver != ADDRESS_ZERO:
            cached_balances[receiver] = cached_balances.get(receiver, 0.0) + convert_to_decimals(value)

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
        logging.info("Getting block data for Terminal Finance tUSDe")
        block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to get_block_balances")
            return block_data

        tusde = w3.eth.contract(
            address=Web3.to_checksum_address(TUSDE_ADDRESS),
            abi=ERC20_ABI,
        )
        sorted_blocks = sorted(blocks)
        cached_block, cached_balances = self.find_closest_cached_data(
            sorted_blocks[0], cached_data
        )
        for target_block in sorted(blocks):
            while cached_block < target_block:
                to_block = min(cached_block + PAGINATION_SIZE, target_block)
                for transfer in self.fetch_transfers(tusde, cached_block + 1, to_block):
                    self.process_transfer(transfer, cached_balances)
                cached_block = to_block

            block_data[target_block] = deepcopy(cached_balances)

        return block_data

if __name__ == "__main__":
    integration = TerminalIntegration(
        integration_id=IntegrationID.EXAMPLE,
        start_block=22000000,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=40000000,
    )

    # Test without cached data
    print("Testing without cached data...")
    without_cached_data_output = integration.get_block_balances(
        cached_data={}, blocks=[22619607, 22619668, 22619716]
    )

    assert without_cached_data_output == {
        22619607: { "0xf651032419e3a19A3f8B1A350427b94356C86Bf4": 3.0 },
        22619668: { "0xf651032419e3a19A3f8B1A350427b94356C86Bf4": 1.0 },
        22619716: { 
            "0xf651032419e3a19A3f8B1A350427b94356C86Bf4": 1.0,
            "0xaFC2a7Dfa6A14a4BbAb663F0966a779458dA123C": 0.0,
        },
    }

    # Test with cached data
    print("Testing with cached data...")
    with_cached_data_output = integration.get_block_balances(
        cached_data= {
            22619716: { "0xf651032419e3a19A3f8B1A350427b94356C86Bf4": 1.0 },
            22790716: {
                "0xf651032419e3a19A3f8B1A350427b94356C86Bf4": 1.0,
                "0xFD46bC7c3025a6864Fccfc9a4e781E4D0D6F3ce5": 3e-6
            }
        },
        blocks=[22790965, 22790912],
    )

    assert with_cached_data_output == {
        22790912: {
            "0xf651032419e3a19A3f8B1A350427b94356C86Bf4": 1.0, 
            "0xFD46bC7c3025a6864Fccfc9a4e781E4D0D6F3ce5": 3e-6,
            "0xfA270DE8C80d37afF947e75968F97F3ABCb39FB0": 499.8
        },
        22790965: {
            "0xf651032419e3a19A3f8B1A350427b94356C86Bf4": 1.0, 
            "0xFD46bC7c3025a6864Fccfc9a4e781E4D0D6F3ce5": 3e-6,
            "0xfA270DE8C80d37afF947e75968F97F3ABCb39FB0": 499.8,
            "0x8484fBedae4E9b2e26Df44b92cD5f81B71C8150E": 542.230021
        }
    }

    print("Tests passed!")