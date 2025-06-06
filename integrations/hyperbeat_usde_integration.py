import json
from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress
from constants.example_integrations import PAGINATION_SIZE
from utils.web3_utils import fetch_events_logs_with_retry, W3_BY_CHAIN

CONTRACT_ADDRESS = Web3.to_checksum_address("0x5eec795d919fa97688fb9844eeb0072e6b846f9d")
ZERO_ADDRESS = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")

try:
    with open("abi/hyperbeat_vault.json") as f:
        CONTRACT_ABI = json.load(f)
except FileNotFoundError:
    CONTRACT_ABI = []
except json.JSONDecodeError:
    CONTRACT_ABI = []


class HyperbeatUSDeIntegration(
    CachedBalancesIntegration
):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain,
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
        if self.chain in W3_BY_CHAIN:
            self.w3 = W3_BY_CHAIN[self.chain]["w3"]
        else:
            raise ValueError(f"Web3 instance not found for chain: {self.chain.value} in W3_BY_CHAIN. Cannot proceed with HyperbeatUSDeIntegration.")
        
        if not CONTRACT_ABI:
            self.contract = None
            self.token_decimals = 18
            return

        try:
            self.contract = self.w3.eth.contract(
                address=CONTRACT_ADDRESS,
                abi=CONTRACT_ABI
            )
        except Exception as e:
            self.contract = None
            self.token_decimals = 18
            return

        try:
            self.token_decimals = self.contract.functions.decimals().call()
        except Exception as e:
            self.token_decimals = 18


    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        result_data: Dict[int, Dict[ChecksumAddress, float]] = {
            b: cached_data[b] for b in blocks if b in cached_data
        }
        
        blocks_to_compute = sorted([b for b in blocks if b not in cached_data])

        if not self.contract or not blocks_to_compute:
            return result_data

        running_raw_balances: Dict[ChecksumAddress, int] = {}
        last_processed_block = self.start_block - 1
        
        available_cache_points = [b for b in cached_data if b < blocks_to_compute[0]]
        if available_cache_points:
            start_point_block = max(available_cache_points)
            last_processed_block = start_point_block
            
            cached_balances = cached_data[start_point_block]
            for addr, float_bal in cached_balances.items():
                running_raw_balances[addr] = int(float_bal * (10**self.token_decimals))
        
        for block_num in blocks_to_compute:
            if block_num < self.start_block:
                result_data[block_num] = {}
                continue

            current_event_from_block = last_processed_block + 1
            while current_event_from_block <= block_num:
                to_block = min(current_event_from_block + PAGINATION_SIZE, block_num)
                
                try:
                    transfer_events = fetch_events_logs_with_retry(
                        f"Hyperbeat USDe Transfers {CONTRACT_ADDRESS}",
                        self.contract.events.Transfer(),
                        current_event_from_block,
                        to_block,
                    )
                except Exception as e:
                    transfer_events = []

                for event in transfer_events:
                    sender = event["args"]["from"]
                    recipient = event["args"]["to"]
                    value_raw = event["args"]["value"]

                    if sender != ZERO_ADDRESS:
                        running_raw_balances[sender] = running_raw_balances.get(sender, 0) - value_raw
                    if recipient != ZERO_ADDRESS:
                        running_raw_balances[recipient] = running_raw_balances.get(recipient, 0) + value_raw
                
                current_event_from_block = to_block + 1
            
            current_block_token_balances: Dict[ChecksumAddress, float] = {}
            for addr, raw_bal in running_raw_balances.items():
                if raw_bal > 0: 
                     current_block_token_balances[addr] = raw_bal / (10**self.token_decimals)

            result_data[block_num] = current_block_token_balances
            
            last_processed_block = block_num
            
        return result_data

    def test_asset_consistency(self, test_block: int):
        if not self.contract:
            return

        calculated_balances_data = self.get_block_balances(cached_data={}, blocks=[test_block])
        
        if test_block not in calculated_balances_data:
            return

        user_balances = calculated_balances_data[test_block]
        sum_calculated_token_balances_float = sum(user_balances.values())
        
        try:
            total_supply_raw = self.contract.functions.totalSupply().call(block_identifier=test_block)
            total_supply_contract_float = total_supply_raw / (10**self.token_decimals)
        except Exception as e:
            return

        tolerance = 1e-5 
        
        if abs(sum_calculated_token_balances_float - total_supply_contract_float) < tolerance:
            print(f"Asset consistency check PASSED for block {test_block}.")
        else:
            print(f"Asset consistency check FAILED for block {test_block}.")
            print(f"   - Calculated sum: {sum_calculated_token_balances_float}")
            print(f"   - Contract totalSupply: {total_supply_contract_float}")


if __name__ == "__main__":
    if not CONTRACT_ABI:
        pass
    else:
        start_block = 3737271
        
        try:
            integration = HyperbeatUSDeIntegration(
                integration_id=IntegrationID.HYPERBEAT_USDE, 
                start_block=start_block, 
                chain=Chain.HYPEREVM,
                summary_cols=[SummaryColumn.TEMPLATE_PTS], 
                excluded_addresses={ZERO_ADDRESS, CONTRACT_ADDRESS},
            )

            if not integration.contract:
                pass
            else:
                test_blocks = [start_block + 100, start_block + 200] 

                balances1 = integration.get_block_balances(
                    cached_data={}, blocks=test_blocks
                )
                print(json.dumps(balances1, indent=2))

                cached_balances_test = {}
                if test_blocks and test_blocks[0] in balances1: 
                    cached_balances_test = {
                        test_blocks[0]: balances1[test_blocks[0]]
                    }
                
                if cached_balances_test:
                    balances2 = integration.get_block_balances(
                        cached_data=cached_balances_test, blocks=[test_blocks[1]]
                    )
                    print(json.dumps(balances2, indent=2))

                if test_blocks:
                    integration.test_asset_consistency(test_block=test_blocks[0])
        except Exception as e:
            print(f"An error occurred during the test run: {e}")
