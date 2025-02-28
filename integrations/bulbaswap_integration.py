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
        self.api_url = "https://api-dev.bulbaswap.io/v1/partner-tasks/ethena/positions"
        # Token addresses for USDE and sUSDE
        self.token_addresses = [
            "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34",  # USDe
            "0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2",  # sUSDe
        ]
        self.page_size = 100  # Configurable page size

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
            
            try:
                # Fetch data for both token addresses
                for token_address in self.token_addresses:
                    page = 0
                    while True:
                        # Get positions data with pagination
                        response = requests.get(
                            self.api_url,
                            params={
                                "tokenAddress": token_address,
                                "blockNumber": block,
                                "page": page,
                                "limit": self.page_size
                            }
                        )
                        data = response.json()
                        
                        if data["code"] == 200 and data["data"]["status"] == 0:
                            positions_data = data["data"]["data"]
                            
                            # Process each user's positions
                            for item in positions_data["items"]:
                                user_address = Web3.to_checksum_address(item["userAddress"])
                                
                                # Sum up liquidity for all pools
                                total_liquidity = 0
                                for pool_data in item["userPositions"].values():
                                    if float(pool_data["liquidityUSD"]) > 0:
                                        total_liquidity += float(pool_data["liquidityUSD"])
                                
                                # Add or update user's total liquidity
                                if total_liquidity > 0:
                                    if user_address in block_data:
                                        block_data[user_address] += total_liquidity
                                    else:
                                        block_data[user_address] = total_liquidity
                            
                            # Check if we've processed all pages
                            pagination = positions_data["pagination"]
                            if page >= pagination["totalPages"] - 1:
                                break
                            page += 1
                        else:
                            print(f"Error in API response for block {block}, token {token_address}")
                            break
                            
            except Exception as e:
                print(f"Error fetching data for block {block}: {str(e)}")
                block_data = {}
            
            result[block] = block_data
            
        return result


if __name__ == "__main__":
    # Simple test
    integration = BulbaswapIntegration(
        integration_id=IntegrationID.BULBASWAP,
        start_block=15817416,
        chain=Chain.ETHEREUM,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        reward_multiplier=1
    )
    
    # Test with a specific block
    result = integration.get_block_balances(
        cached_data={},
        blocks=[15817416]
    )
    print("Block balances:", result)
