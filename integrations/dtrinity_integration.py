import logging
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from web3 import Web3

from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from constants.chains import Chain
from utils import abi
from utils.address import to_checksum_address

logger = logging.getLogger(__name__)

# Contract addresses for dTrinity on Fraxtal
USDE_ATOKEN_ADDRESS = "0x1234567890123456789012345678901234567890"  
SUSDE_ATOKEN_ADDRESS = "0x0987654321098765432109876543210987654321"  
LENDING_POOL_ADDRESS = "0xABCDEF1234567890ABCDEF1234567890ABCDEF12"  

# Block where the dTrinity contracts were deployed on Fraxtal
DTRINITY_GENESIS_BLOCK = 1000000  


class DTrinityIntegration(CachedBalancesIntegration):
    """
    Integration for dTrinity lending platform on Fraxtal.
    Tracks user balances of supplied USDe and sUSDe.
    """

    def __init__(self):
        super().__init__(
            integration_id=IntegrationID.DTRINITY_USDE,
            chain=Chain.FRAXTAL,
            genesis_block=DTRINITY_GENESIS_BLOCK,
        )
        self.usde_integration = IntegrationID.DTRINITY_USDE
        self.susde_integration = IntegrationID.DTRINITY_SUSDE
        
        # Load ABIs
        self.atoken_abi = abi.get_abi("abi/atoken.json")
        self.lending_pool_abi = abi.get_abi("abi/lending_pool.json")
        
        # Create contract instances
        self.usde_atoken = self.web3.eth.contract(
            address=Web3.to_checksum_address(USDE_ATOKEN_ADDRESS),
            abi=self.atoken_abi
        )
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
        Get user balances for the specified blocks.
        Returns a dictionary of {block_number: {address: balance}}
        """
        result = {}
        
        # Process blocks in order
        sorted_blocks = sorted(block_numbers)
        
        for block in sorted_blocks:
            logger.debug(f"Processing block {block} for dTrinity integration")
            
            # Skip if we already have data for this block
            if block in previous_balances:
                result[block] = previous_balances[block]
                continue
                
            # Get all Supply events since the last processed block
            last_processed_block = max([b for b in previous_balances.keys() if b < block] or [self.genesis_block])
            
            # Get all supplier addresses that may have changed their balances
            users_to_check = self._get_active_users(last_processed_block, block)
            
            # Get balances for each integration (USDe and sUSDe)
            usde_balances = self._get_user_balances(users_to_check, block, self.usde_atoken)
            susde_balances = self._get_user_balances(users_to_check, block, self.susde_atoken)
            
            # Store in results for both integrations
            self.store_balances(block, usde_balances, result, self.usde_integration)
            self.store_balances(block, susde_balances, result, self.susde_integration)
            
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
            users.add(to_checksum_address(event.args.user))
            
        return list(users)
    
    def _get_user_balances(self, users: List[str], block: int, atoken_contract) -> Dict[str, Decimal]:
        """
        Get user balances for a specific aToken at a specific block.
        """
        balances = {}
        
        for user in users:
            try:
                # Call balanceOf for each user
                balance_raw = atoken_contract.functions.balanceOf(user).call(block_identifier=block)
                # Convert to decimal, assuming 18 decimals (standard for aTokens)
                balance = Decimal(balance_raw) / Decimal(10**18)
                balances[user] = balance
            except Exception as e:
                logger.error(f"Error getting balance for {user} at block {block}: {e}")
                
        return balances
        
    def store_balances(
        self, 
        block: int, 
        balances: Dict[str, Decimal], 
        result: Dict[int, Dict[str, Decimal]],
        integration_id: IntegrationID
    ):
        """
        Store balances for a specific integration ID
        """
        if integration_id not in result:
            result[integration_id] = {}
            
        result[integration_id][block] = balances


# Add basic tests that we can run to verify the integration works
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    integration = DTrinityIntegration()
    
    # Test with a recent block
    latest_block = integration.web3.eth.block_number
    test_blocks = [latest_block]
    
    # Run the integration with empty previous balances
    block_balances = integration.get_block_balances(test_blocks, {})
    
    # Print the results
    for block, balances in block_balances.items():
        balance_count = len(balances)
        total_balance = sum(balances.values())
        print(f"Block {block}: {balance_count} users with total balance {total_balance}") 