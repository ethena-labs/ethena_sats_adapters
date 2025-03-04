import logging
from typing import Dict, List
from decimal import Decimal

from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from constants.chains import Chain
from constants.dtrinity import SUSDE_GENESIS_BLOCK, SUSDE_ATOKEN_ADDRESS
from utils import dtrinity

logger = logging.getLogger(__name__)

class DTrinitySUSDEIntegration(CachedBalancesIntegration):
    """
    Integration for dTrinity lending platform on Fraxtal.
    Tracks user balances of supplied sUSDe.
    """

    def __init__(self):
        super().__init__(
            integration_id=IntegrationID.DTRINITY_SUSDE,
            chain=Chain.FRAXTAL,
            genesis_block=SUSDE_GENESIS_BLOCK,
        )
        
        # Create contract instances
        self.lending_pool = dtrinity.get_lending_pool_contract(self.web3)
        self.susde_atoken = dtrinity.get_atoken_contract(self.web3, SUSDE_ATOKEN_ADDRESS)

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
            users_to_check = dtrinity.get_active_users(self.lending_pool, last_processed_block, block)
            
            # Get balances for sUSDe
            susde_balances = dtrinity.get_user_balances(users_to_check, block, self.susde_atoken)
            
            # Store results
            result[block] = susde_balances
            
        return result


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