from typing import Dict, List, Optional, Set
import requests
from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID

class BulbaswapIntegration(CachedBalancesIntegration):
    """Integration for tracking Bulbaswap LP positions."""
    
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
        ethereal_multiplier_func: Optional[callable] = None,
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
        self.api_url = "https://api.bulbaswap.io/v1/partner-tasks/ethena/positions"
        self.target_address = None

    def set_target_address(self, address: str) -> None:
        """Set the target address for querying positions.

        Args:
            address: The Ethereum address to query positions for.
        """
        self.target_address = Web3.to_checksum_address(address)

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Get user balances for specified blocks, using cached data when available.

        Args:
            cached_data: Dictionary mapping block numbers to user balances at that block.
            blocks: List of block numbers to get balances for.

        Returns:
            Dictionary mapping block numbers to user balances.
        """
        result = {}
        
        for block in blocks:
            # Skip if we already have data for this block
            if block in cached_data:
                result[block] = cached_data[block]
                continue
                
            block_data = {}
            
            # Get the address from the request
            if not hasattr(self, 'target_address'):
                raise ValueError("target_address is required. Set it using set_target_address() method.")
            
            try:
                # Get user's positions data
                response = requests.get(
                    self.api_url,
                    params={
                        "address": self.target_address,
                        "blockNumber": block
                    }
                )
                data = response.json()
                
                if data["code"] == 200 and data["data"]["status"] == 0:
                    positions_data = data["data"]["data"]
                    total_liquidity = 0
                    
                    # Sum V2 positions
                    for pool_data in positions_data.get("v2Positions", {}).values():
                        if float(pool_data["liquidityUSD"]) > 0:
                            total_liquidity += float(pool_data["liquidityUSD"])
                    
                    # Sum V3 positions
                    for pool_data in positions_data.get("v3Positions", {}).values():
                        if float(pool_data["liquidityUSD"]) > 0:
                            total_liquidity += float(pool_data["liquidityUSD"])
                    
                    # Only add to result if user has liquidity
                    if total_liquidity > 0:
                        block_data[Web3.to_checksum_address(self.target_address)] = total_liquidity
                            
            except Exception as e:
                print(f"Error fetching data for block {block}: {str(e)}")
                block_data = {}
            
            result[block] = block_data
            
        return result


if __name__ == "__main__":
    # Simple test
    integration = BulbaswapIntegration(
        integration_id=IntegrationID.BULBASWAP,
        start_block=3000000,
        chain=Chain.ETHEREUM,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        reward_multiplier=1
    )
    
    # Set target address for testing
    integration.set_target_address("0xB6702191769266D18F69e1d00B5E73f0D181b75E")
    
    # Test with a specific block
    result = integration.get_block_balances(
        cached_data={},
        blocks=[3000000]
    )
    print("Block balances:", result)
    
    # Example output format:
    # {
    #     3000000: {
    #         "0xB6702191769266D18F69e1d00B5E73f0D181b75E": 82701.265912
    #     }
    # }
