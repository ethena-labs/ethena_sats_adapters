from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from copy import deepcopy
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from eth_typing import ChecksumAddress
import logging
from constants.hl_hyperdrive import (
    HYPERDRIVE_USDE_MARKET_ADDRESS,
    HYPERDRIVE_USDE_START_BLOCK,
    LOG_QUERY_BLOCK_CHUNK_SIZE
)
from utils.web3_utils import fetch_events_logs_with_retry
from web3 import Web3
from utils.web3_utils import HYPEREVM_NODE_URL
import json
with open("abi/ERC20_abi.json") as f:
    ERC20_ABI = json.load(f)
    
logging.basicConfig(level=logging.INFO)

class HlHyperdriveIntegration(
    CachedBalancesIntegration
):
    def __init__(
        self,
        integration_id: IntegrationID,
        chain: Chain = Chain.HYPEREVM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block: Optional[int] = None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func: Optional[Callable[[int, str], int]] = None,
        start_block_override: Optional[int] = None,
    ):
        start_block = (
            start_block_override
            if start_block_override is not None
            else HYPERDRIVE_USDE_START_BLOCK
        )
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
        
        self.w3 = Web3(Web3.HTTPProvider(HYPEREVM_NODE_URL))
        if not self.w3.is_connected():
            logging.error(f"Failed to connect to RPC at {HYPEREVM_NODE_URL}")
            raise ConnectionError(f"Could not connect to HyperEVM RPC at {HYPEREVM_NODE_URL}")
        logging.info(f"Connected to HyperEVM RPC at {HYPEREVM_NODE_URL}")
            
        self.usde_market_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(HYPERDRIVE_USDE_MARKET_ADDRESS),
            abi=ERC20_ABI
        )

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block data for Hyperdrive USDe")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to Hyperdrive USDe get_block_balances")
            return new_block_data

        sorted_blocks = sorted(blocks)
        cache_copy: Dict[int, Dict[ChecksumAddress, float]] = deepcopy(cached_data)

        for block in sorted_blocks:
            sorted_existing_blocks = sorted(
                cache_copy,
                reverse=True,
            )
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
                to_block = min(start + LOG_QUERY_BLOCK_CHUNK_SIZE, block)
                transfers = fetch_events_logs_with_retry(
                    "Token transfers claimed Hyperdrive USDe",
                    self.usde_market_contract.events.Transfer(),
                    start,
                    to_block,
                )
                for transfer in transfers:
                    sender = transfer["args"]["from"]
                    recipient = transfer["args"]["to"]
                    amount = transfer["args"]["value"]
                    
                    if recipient == "0x0000000000000000000000000000000000000000":
                        if sender not in bals:
                            bals[sender] = 0
                        bals[sender] -= amount
                    else:
                        if recipient not in bals:
                            bals[recipient] = 0
                        bals[recipient] += transfer["args"]["value"]
                start = to_block + 1
            new_block_data[block] = bals
            cache_copy[block] = bals

        return new_block_data


if __name__ == "__main__":
    example_integration = HlHyperdriveIntegration(
        integration_id=IntegrationID.HL_HYPEDRIVE,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        start_block_override=5244072,
        end_block=40000000,
    )
    
    latest_block = example_integration.w3.eth.block_number
    print(f"Latest block on HyperEVM network: {latest_block}")

    without_cached_data_output = example_integration.get_block_balances(
        cached_data={}, blocks=[5244072, 5245226, 5248412]
    )

    print("=" * 120)
    print("Run without cached data", without_cached_data_output)
    print("=" * 120, "\n" * 5)