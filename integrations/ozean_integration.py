from copy import deepcopy
import logging
from typing import Dict, List, Optional
from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from constants.ozean import (
    LGE_CONTRACT,
    SUSDE_TOKEN_ADDRESS,
    OZEAN_LGE_DEPLOYMENT_BLOCK,
    PAGINATION_SIZE
)
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import fetch_events_logs_with_retry

class OzeanIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID = IntegrationID.OZEAN_LGE,
        start_block: int = OZEAN_LGE_DEPLOYMENT_BLOCK,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 20,
    ):
        if summary_cols is None:
            summary_cols = [SummaryColumn.OZEAN_LGE_POINTS]
            
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier
        )
        
        self.contract = LGE_CONTRACT

    def get_block_balances(
        self,
        cached_data: Dict[int, Dict[ChecksumAddress, float]],
        blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        
        try:
            deposit_events = fetch_events_logs_with_retry(
                "Deposit events",
                self.contract.events.Deposit(),
                from_block=self.start_block,
                to_block=max(blocks),
                filter={"_token": SUSDE_TOKEN_ADDRESS}
            )
            
            withdraw_events = fetch_events_logs_with_retry(
                "Withdraw events",
                self.contract.events.Withdraw(),
                from_block=self.start_block,
                to_block=max(blocks),
                filter={"_token": SUSDE_TOKEN_ADDRESS}
            )
            
            all_events = []
            for event in deposit_events:
                all_events.append({
                    'type': 'Deposit',
                    'block': event['blockNumber'],
                    'address': Web3.to_checksum_address(event['args']['_to']),
                    'amount': float(event['args']['_amount']) / 10**18
                })
                
            for event in withdraw_events:
                all_events.append({
                    'type': 'Withdraw',
                    'block': event['blockNumber'],
                    'address': Web3.to_checksum_address(event['args']['_to']),
                    'amount': float(event['args']['_amount']) / 10**18
                })
                
            all_events.sort(key=lambda x: x['block'])

            balances: Dict[ChecksumAddress, float] = {}
            current_event_idx = 0
            
            for block in sorted(blocks):
                if block < self.start_block:
                    new_block_data[block] = {}
                    continue
                    
                while (current_event_idx < len(all_events) and all_events[current_event_idx]['block'] <= block):
                    event = all_events[current_event_idx]
                    address = event['address']
                    
                    if event['type'] == 'Deposit':
                        balances[address] = balances.get(address, 0) + event['amount']
                    else:
                        balances[address] = max(0, balances.get(address, 0) - event['amount'])
                        
                    current_event_idx += 1
                
                block_balances = {
                    addr: bal for addr, bal in balances.items() if bal > 0
                }
                new_block_data[block] = block_balances
            
            return new_block_data
            
        except Exception as e:
            logging.error(f"Error in get_block_balances: {e}")
            raise e


if __name__ == "__main__":
    integration = OzeanIntegration()
    
    blocks_to_test = [21893209, 21940405, 21940416]
    result = integration.get_block_balances({}, blocks_to_test)
    print("Results without cache:", result)
    
    # Test with cached data
    cached_blocks = {21893209: result[21893209]}
    result_with_cache = integration.get_block_balances(cached_blocks, [21940417])
    print("\nResults with cache:", result_with_cache) 