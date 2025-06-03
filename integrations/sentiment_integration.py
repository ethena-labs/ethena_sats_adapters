import logging
import os
from typing import Dict, List, Optional, Set
from eth_typing import ChecksumAddress
from web3 import Web3
from eth_abi import decode as eth_abi_decode
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from constants.sentiment import (
    SENTIMENT_USDE_SUPERPOOL_ADDRESS, 
    SENTIMENT_USDE_SUPERPOOL_START_BLOCK
)
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.slack import slack_message
from utils.web3_utils import HYPEREVM_NODE_URL

# SuperPool ABI for balanceOf, totalSupply, Transfer events
SUPERPOOL_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "account",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "shares",
                "type": "uint256"
            }
        ],
        "name": "previewRedeem",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "from",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "Transfer",
        "type": "event"
    }
]

# Cache of all holders - maintains a set of all addresses that have ever held SuperPool tokens
ALL_HOLDERS_CACHE = set()

class SentimentIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            excluded_addresses=excluded_addresses
        )
        # Initialize Web3 provider - use HYPEREVM_NODE_URL from environment variables
        self.w3 = Web3(Web3.HTTPProvider(HYPEREVM_NODE_URL))
        if not self.w3.is_connected():
            logging.error(f"Failed to connect to RPC at {HYPEREVM_NODE_URL}")
            raise ConnectionError(f"Could not connect to HyperEVM RPC at {HYPEREVM_NODE_URL}")
        logging.info(f"Connected to HyperEVM RPC at {HYPEREVM_NODE_URL}")
            
        # Initialize SuperPool contract
        self.superpool_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(SENTIMENT_USDE_SUPERPOOL_ADDRESS),
            abi=SUPERPOOL_ABI
        )
        # Initialize cache for known holders (addresses that have interacted with the contract)
        self.known_holders = ALL_HOLDERS_CACHE
        
    def get_transfer_events(self, from_block: int, to_block: int) -> Set[ChecksumAddress]:
        """Get unique addresses involved in Transfer events between the given blocks."""
        logging.info(f"[Sentiment integration] Getting Transfer events from block {from_block} to {to_block}")
        
        try:
            # Create transfer event signature
            transfer_event = self.superpool_contract.events.Transfer
            
            # Get all transfer events in the block range
            events = transfer_event.get_logs(fromBlock=from_block, toBlock=to_block)
            
            # Extract unique addresses from 'from' and 'to' fields
            addresses = set()
            for event in events:
                addresses.add(Web3.to_checksum_address(event.args['from']))
                addresses.add(Web3.to_checksum_address(event.args['to']))
                
            # Remove zero address (mint/burn operations)
            if Web3.to_checksum_address('0x0000000000000000000000000000000000000000') in addresses:
                addresses.remove(Web3.to_checksum_address('0x0000000000000000000000000000000000000000'))
                
            return addresses
            
        except Exception as e:
            error_msg = f"Error fetching Transfer events from block {from_block} to {to_block}: {e}"
            logging.error(error_msg)
            slack_message(error_msg)
            return set()
            
    def update_holder_cache(self, latest_block: int):
        """Update cache with all addresses that have interacted with the contract."""
        if not self.known_holders:
            # If the cache is empty, get all historical holders
            logging.info("[Sentiment integration] Initializing holder cache")
            try:
                # Chunk size for event lookups (to avoid exceeding block range limits)
                chunk_size = 10000
                
                # Process block range in chunks
                start = SENTIMENT_USDE_SUPERPOOL_START_BLOCK
                while start < latest_block:
                    end = min(start + chunk_size, latest_block)
                    new_addresses = self.get_transfer_events(start, end)
                    self.known_holders.update(new_addresses)
                    start = end + 1
                    
                logging.info(f"[Sentiment integration] Found {len(self.known_holders)} historical holders")
                
                # Update global cache
                ALL_HOLDERS_CACHE.update(self.known_holders)
                
            except Exception as e:
                error_msg = f"Error updating holder cache: {e}"
                logging.error(error_msg)
                slack_message(error_msg)
    
    def batch_get_balances(self, addresses: List[ChecksumAddress], block_number: int) -> Dict[ChecksumAddress, float]:
        """Use multicall to batch get balances for multiple addresses."""
        results: Dict[ChecksumAddress, float] = {}
        
        if not addresses:
            return results
            
        try:
            # Fall back to individual queries instead of multicall
            # This simplifies the code and avoids decoding issues
            for address in addresses:
                try:
                    # Get SuperPool token shares balance
                    balance = self.superpool_contract.functions.balanceOf(address).call(
                        block_identifier=block_number
                    )
                    if balance > 0:
                        # Convert SuperPool shares to underlying USDE amount using previewRedeem
                        usde_amount = self.superpool_contract.functions.previewRedeem(balance).call(
                            block_identifier=block_number
                        )
                        # Normalize by dividing by 1e18
                        usde_balance = float(usde_amount) / 1e18
                        results[address] = usde_balance
                except Exception as e:
                    logging.error(f"Error getting balance for address {address}: {e}")
                    continue
                    
            return results
                
        except Exception as e:
            error_msg = f"Error batch getting balances at block {block_number}: {e}"
            logging.error(error_msg)
            slack_message(error_msg)
            return {}
        
    def get_holders_for_block(self, block_number: int) -> Dict[ChecksumAddress, float]:
        """Gets all holders and their balances for a specific block."""
        logging.info(f"[Sentiment integration] Getting holders for block {block_number}")
        
        try:
            # Update holder cache if needed
            if not self.known_holders:
                self.update_holder_cache(block_number)
                
            if not self.known_holders:
                return {}
                
            # Use batch queries to efficiently get balances for all holders
            # Process in chunks to avoid request size limits
            all_holders = list(self.known_holders)
            holders_data: Dict[ChecksumAddress, float] = {}
            
            # Process in chunks of 100 addresses
            chunk_size = 100
            for i in range(0, len(all_holders), chunk_size):
                chunk = all_holders[i:i+chunk_size]
                chunk_balances = self.batch_get_balances(chunk, block_number)
                holders_data.update(chunk_balances)
                
            return holders_data
            
        except Exception as e:
            error_msg = f"Error fetching Sentiment USDE SuperPool holders for block {block_number}: {e}"
            logging.error(error_msg)
            slack_message(error_msg)
            return {}

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """
        Get user balances for specified blocks, using cached data when available.
        
        Args:
            cached_data: Dictionary mapping block numbers to user balances at that block
            blocks: List of block numbers to get balances for
            
        Returns:
            Dictionary mapping block numbers to user balances at that block
        """
        logging.info("[Sentiment integration] Getting block balances")
        
        # Initialize result dictionary
        result_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        
        # Process each block
        for block in blocks:
            # Skip blocks before the start block
            if block < self.start_block:
                result_data[block] = {}
                continue
                
            # Use cached data if available
            if block in cached_data and cached_data[block]:
                logging.info(f"[Sentiment integration] Using cached data for block {block}")
                result_data[block] = cached_data[block]
                continue
                
            # Get fresh data for this block
            logging.info(f"[Sentiment integration] Fetching data for block {block}")
            holders_data = self.get_holders_for_block(block)
            result_data[block] = holders_data
        
        return result_data


if __name__ == "__main__":
    """
    Test script for the Sentiment USDE SuperPool integration.
    This is for development/testing only and not used when the integration is run as part of the Ethena system.
    """
    import sys
    from constants.summary_columns import SummaryColumn
    
    print("Sentiment Protocol USDE SuperPool Integration Test")
    print("=" * 50)
    print(f"SuperPool Address: {SENTIMENT_USDE_SUPERPOOL_ADDRESS}")
    print(f"RPC URL: {HYPEREVM_NODE_URL}")
    print(f"Start Block: {SENTIMENT_USDE_SUPERPOOL_START_BLOCK}")
    print("-" * 50)
    
    # Create the integration
    test_integration = SentimentIntegration(
        integration_id=IntegrationID.SENTIMENT_USDE,
        start_block=SENTIMENT_USDE_SUPERPOOL_START_BLOCK,
        chain=Chain.HYPEREVM,
        summary_cols=[SummaryColumn.SENTIMENT_USDE_PTS],
        reward_multiplier=1
    )
    
    # Test RPC connection
    try:
        latest_block = test_integration.w3.eth.block_number
        print(f"Successfully connected to HyperEVM - Latest Block: {latest_block}")
    except Exception as e:
        print(f"Failed to connect to HyperEVM RPC: {e}")
        sys.exit(1)
        
    # Test contract connection
    try:
        total_supply = test_integration.superpool_contract.functions.totalSupply().call()
        print(f"Successfully connected to SuperPool contract - Total Supply: {total_supply / 1e18:.2f}")
    except Exception as e:
        print(f"Failed to interact with SuperPool contract: {e}")
        sys.exit(1)
    
    # Define test blocks
    test_block = latest_block - 100  # 100 blocks ago
    test_blocks = [
        SENTIMENT_USDE_SUPERPOOL_START_BLOCK,   # Starting block
        latest_block - 5000,                    # Historical block
        latest_block - 100,                     # Recent block
        latest_block                            # Latest block
    ]
    
    # Test with a single block first
    print("\nTesting with a single block...")
    print(f"Block: {test_block}")
    
    try:
        result = test_integration.get_block_balances(cached_data={}, blocks=[test_block])
        
        # Print results
        holders = result.get(test_block, {})
        holder_count = len(holders)
        print(f"Found {holder_count} holders with non-zero balances")
        
        if holder_count > 0:
            print("\nTop 5 holders by balance:")
            sorted_holders = sorted(holders.items(), key=lambda x: x[1], reverse=True)[:5]
            for address, balance in sorted_holders:
                print(f"  {address}: {balance:.6f} USDE")
        else:
            print("No holders found. This could be due to no deposits in the pool or issues with the implementation.")
    
    except Exception as e:
        print(f"Error during single block test: {e}")
    
    # Test with multiple blocks
    print("\nTesting with multiple blocks...")
    for block in test_blocks:
        print(f"Testing block {block}...")
        try:
            result = test_integration.get_block_balances(cached_data={}, blocks=[block])
            holder_count = len(result.get(block, {}))
            print(f"  Block {block}: {holder_count} holders with non-zero balances")
        except Exception as e:
            print(f"  Error testing block {block}: {e}")
    
    # Test caching functionality
    print("\nTesting cached data functionality...")
    cached_data = {test_block: {"0x1234567890123456789012345678901234567890": 100.0}}
    
    try:
        result = test_integration.get_block_balances(cached_data=cached_data, blocks=[test_block])
        print(f"Successfully used cached data for block {test_block}")
        print(f"Cached holders: {list(result[test_block].keys())}")
    except Exception as e:
        print(f"Error during cache test: {e}")
    
    print("\nIntegration test completed") 