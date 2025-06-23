import requests
from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress
from collections import defaultdict


class TimeswapIntegration(CachedBalancesIntegration):
    """
    Integration for Timeswap protocol to track USDe lending positions for Ethena Points Campaign.
    
    This integration fetches data from the Timeswap API and calculates user balances
    based on their lending activities in USDe pools.
    """
    
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.HYPEREVM,
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
        
        # API endpoint for Timeswap pool data
        self.api_url = "https://timeswap-pool-details.vercel.app/api/usde-pool-details"

    def _calculate_user_balances_from_transactions(self, transactions: List[Dict]) -> Dict[ChecksumAddress, float]:
        """
        Calculate current user balances based on transaction history.
        
        Args:
            transactions: List of transaction data from API
            
        Returns:
            Dict mapping user addresses to their current lending balances
        """
        user_balances = defaultdict(float)
        
        # Sort transactions by timestamp to process in chronological order
        transactions.sort(key=lambda x: int(x.get("txn_timestamp", 0)))
        
        for tx in transactions:
            try:
                address = Web3.to_checksum_address(tx["txn_from"])
                tx_type = tx["txn_type"]
                
                # Skip excluded addresses
                if self.excluded_addresses and address in self.excluded_addresses:
                    continue
                
                # Process different transaction types
                if tx_type == "LendGivenPrincipal":
                    # User is lending tokens
                    token1_lent = tx.get("token1_amount_lent")
                    if token1_lent:
                        # Convert scientific notation to float
                        amount = float(token1_lent)
                        user_balances[address] += amount
                        
                elif tx_type == "CloseLendGivenPosition":
                    # User is closing lending position
                    token1_redeemed = tx.get("closelend_token1_amount_redeemed")
                    if token1_redeemed:
                        amount = float(token1_redeemed)
                        user_balances[address] = max(0, user_balances[address] - amount)
                        
                elif tx_type == "AddLiquidityGivenPrincipal":
                    # User is adding liquidity
                    token1_added = tx.get("token1_amount_added")
                    if token1_added:
                        amount = float(token1_added)
                        user_balances[address] += amount
                        
                elif tx_type == "RemoveLiquidityGivenPosition":
                    # User is removing liquidity
                    token1_removed = tx.get("token1_amount_removed")
                    if token1_removed:
                        amount = float(token1_removed)
                        user_balances[address] = max(0, user_balances[address] - amount)
                        
            except (ValueError, KeyError, TypeError) as e:
                print(f"Error processing transaction {tx.get('transaction_hash', 'unknown')}: {e}")
                continue
        
        # Convert to more reasonable units and filter small amounts
        processed_balances = {}
        for address, balance in user_balances.items():
            if balance > 0:
                # Convert to more reasonable units (assuming 18 decimals for USDe)
                normalized_balance = balance / (10 ** 18)
                if normalized_balance > 1:  # Minimum threshold to avoid dust
                    processed_balances[address] = normalized_balance
        
        return processed_balances

    def get_block_balances(
    self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
) -> Dict[int, Dict[ChecksumAddress, float]]:
        """
        Get user balances for specified blocks, using cached data when available.

        Args:
            cached_data: Dictionary mapping block numbers to user balances at that block
            blocks: List of block numbers to get balances for

        Returns:
            Dictionary mapping block numbers to user balances
        """
        result = {}
        blocks_needing_data = []
        
        # First pass: collect cached data and identify blocks needing fresh data
        for block in blocks:
            if block in cached_data:
                result[block] = cached_data[block]
            else:
                blocks_needing_data.append(block)
        
        # If no blocks need fresh data, return early
        if not blocks_needing_data:
            return result
        
        # Make API call ONCE for all blocks that need data
        try:
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success") and data.get("data"):
                # Calculate balances from transaction history
                block_data = self._calculate_user_balances_from_transactions(data["data"])
                
                # Apply the same data to all blocks needing it
                for block in blocks_needing_data:
                    result[block] = block_data
            else:
                print("Invalid API response")
                # Set empty data for all blocks that failed
                for block in blocks_needing_data:
                    result[block] = {}
                    
        except requests.RequestException as e:
            print(f"Error fetching Timeswap data: {e}")
            # Set empty data for all blocks that failed
            for block in blocks_needing_data:
                result[block] = {}
        except Exception as e:
            print(f"Error processing data: {e}")
            # Set empty data for all blocks that failed
            for block in blocks_needing_data:
                result[block] = {}
        
        return result

if __name__ == "__main__":
    timeswap_integration = TimeswapIntegration(
        integration_id=IntegrationID.TIMESWAP, 
        start_block=400000,
        summary_cols=[SummaryColumn.TIMESWAP_USDE_PTS],  
        chain=Chain.HYPEREVM,
        reward_multiplier=1,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=21000000,
    )
    
    print("Testing Timeswap Integration...")
    
    # Test with no cached data
    result = timeswap_integration.get_block_balances(
        cached_data={}, 
        blocks=[20500000, 20500001]
    )
    
    print(f"Number of blocks processed: {len(result)}")
    for block, balances in result.items():
        print(f"Block {block}: {len(balances)} users with balances")
        # Show top 3 users by balance
        if balances:
            top_users = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:3]
            for addr, balance in top_users:
                print(f"  {addr}: {balance:.6f} USDe")
    
    # Test with cached data
    cached_result = timeswap_integration.get_block_balances(
        cached_data={20500000: result.get(20500000, {})},
        blocks=[20500000, 20500002]  # One cached, one new
    )
    
    print(f"\nCached test - Blocks processed: {len(cached_result)}")
    print("Cache working correctly:", cached_result[20500000] == result[20500000])