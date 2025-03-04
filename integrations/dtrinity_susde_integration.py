import logging
from typing import Dict, List
from decimal import Decimal
from web3 import Web3

from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from constants.chains import Chain
from utils import abi

logger = logging.getLogger(__name__)

# Contract addresses for dTrinity on Fraxtal
SUSDE_ATOKEN_ADDRESS = "0x12ED58F0744dE71C39118143dCc26977Cb99cDef"  
LENDING_POOL_ADDRESS = "0xD76C827Ee2Ce1E37c37Fc2ce91376812d3c9BCE2"  

# Block where the dTrinity contracts were deployed on Fraxtal
DTRINITY_GENESIS_BLOCK = 13799261  


class DTrinitySUSDEIntegration(CachedBalancesIntegration):
    """
    Integration for dTrinity lending platform on Fraxtal.
    Tracks user balances of supplied sUSDe.
    """

    def __init__(self):
        super().__init__(
            integration_id=IntegrationID.DTRINITY_SUSDE,
            chain=Chain.FRAXTAL,
            genesis_block=DTRINITY_GENESIS_BLOCK,
        )
        
        # Load ABIs
        self.atoken_abi = abi.get_abi("abi/dtrinity_atoken.json")
        self.lending_pool_abi = abi.get_abi("abi/dtrinity_lending_pool.json")
        
        # Create contract instances
        self.susde_atoken = self.web3.eth.contract(
            address=Web3.to_checksum_address(SUSDE_ATOKEN_ADDRESS),
            abi=self.atoken_abi
        )
        self.lending_pool = self.web3.eth.contract(
            address=Web3.to_checksum_address(LENDING_POOL_ADDRESS),
            abi=self.lending_pool_abi
        )

    def get_block_balances(
        self, 
        block_numbers: List[int], 
        previous_balances: Dict[int, Dict[str, Decimal]]
    ) -> Dict[int, Dict[str, Decimal]]:
        """
        Get sUSDe user balances for the specified blocks.
        Returns a dictionary of {block_number: {address: balance}}
        """
        result = {}
        
        # Process blocks in order
        sorted_blocks = sorted(block_numbers)
        
        for block in sorted_blocks:
            logger.debug(f"Processing block {block} for dTrinity sUSDe integration")
            
            # Skip if we already have data for this block
            if block in previous_balances:
                result[block] = previous_balances[block]
                continue
                
            # Get all Supply events since the last processed block
            last_processed_block = max([b for b in previous_balances.keys() if b < block] or [self.genesis_block])
            
            # Get all supplier addresses that may have changed their balances
            users_to_check = self._get_active_users(last_processed_block, block)
            
            # Get balances for sUSDe
            susde_balances = self._get_user_balances(users_to_check, block)
            
            # Store results
            result[block] = susde_balances
            
        return result
    
    def _get_active_users(self, from_block: int, to_block: int) -> List[str]:
        """
        Get a list of users who have had any activity in the given block range.
        This is optimized by looking for relevant events instead of checking all users.
        """
        # Look for deposit/withdrawal events in the lending pool
        deposit_events = self.lending_pool.events.Supply().get_logs(fromBlock=from_block, toBlock=to_block)
        withdraw_events = self.lending_pool.events.Withdraw().get_logs(fromBlock=from_block, toBlock=to_block)
        
        # Extract unique user addresses
        users = set()
        for event in deposit_events + withdraw_events:
            users.add(Web3.to_checksum_address(event.args.user))
            
        return list(users)
    
    def _get_user_balances(self, users: List[str], block: int) -> Dict[str, Decimal]:
        """
        Get user balances for sUSDe aToken at a specific block.
        """
        balances = {}
        
        for user in users:
            try:
                # Call balanceOf for each user
                balance_raw = self.susde_atoken.functions.balanceOf(user).call(block_identifier=block)
                # Convert to decimal, assuming 18 decimals (standard for aTokens)
                balance = Decimal(balance_raw) / Decimal(10**18)
                balances[user] = balance
            except Exception as e:
                logger.error(f"Error getting sUSDe balance for {user} at block {block}: {e}")
                
        return balances


# Add basic tests that we can run to verify the integration works
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    integration = DTrinitySUSDEIntegration()
    
    # Test with a recent block
    latest_block = integration.web3.eth.block_number
    test_blocks = [latest_block]
    
    # Run the integration with empty previous balances
    block_balances = integration.get_block_balances(test_blocks, {})
    
    # Print the results
    for block, balances in block_balances.items():
        balance_count = len(balances)
        total_balance = sum(balances.values())
        print(f"Block {block}: {balance_count} users with total sUSDe balance {total_balance}") 