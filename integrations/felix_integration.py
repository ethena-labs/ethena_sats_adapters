import logging
from typing import Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress
from utils.felix import get_users_asset_balances_at_block_multithreaded


class FelixUsdeIntegration(CachedBalancesIntegration):    
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.HYPEREVM,
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
            excluded_addresses=excluded_addresses,
        )


    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Get user balances for specified blocks, using cached data when available.

        Args:
            cached_data (Dict[int, Dict[ChecksumAddress, float]]): Dictionary mapping block numbers
                to user balances at that block. Used to avoid recomputing known balances.
                The inner dictionary maps user addresses to their USDe balance.
            blocks (List[int]): List of block numbers to get balances for.

        Returns:
            Dict[int, Dict[ChecksumAddress, float]]: Dictionary mapping block numbers to user balances,
                where each inner dictionary maps user addresses to their USDe balance
                at that block.
        """
        logging.info("[Felix integration] Getting block balances")
        
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
                logging.info(f"[Felix integration] Using cached data for block {block}")
                result_data[block] = cached_data[block]
                continue
                
            # Get fresh data for this block
            logging.info(f"[Felix integration] Fetching data for block {block}")
            try:
                block_balances = get_users_asset_balances_at_block_multithreaded(block)
                result_data[block] = block_balances
            except Exception as e:
                logging.error(f"[Felix integration] Error fetching data for block {block}: {e}")
                result_data[block] = {}
        
        return result_data


if __name__ == "__main__":
    """
    Test script for the Felix USDe integration.
    This is for development/testing only and not used when the integration is run as part of the Ethena system.
    """
    # Create example integration
    example_integration = FelixUsdeIntegration(
        integration_id=IntegrationID.FELIX_USDE,
        start_block=3450891,
        summary_cols=[SummaryColumn.FELIX_USDE_PTS],
        chain=Chain.HYPEREVM,
        reward_multiplier=1,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
    )
    
    # Test without cached data
    print("Testing Felix USDe Integration")
    print("=" * 50)
    
    test_blocks = [10200000, 10200001, 10200002]
    without_cached_data_output = example_integration.get_block_balances(
        cached_data={}, blocks=test_blocks
    )
    print("Without cached data:")
    print(without_cached_data_output)
    print()
    
    # Test with cached data
    cached_data = {
        10200000: {
            Web3.to_checksum_address("0x1234567890123456789012345678901234567890"): 100.0,
            Web3.to_checksum_address("0x2345678901234567890123456789012345678901"): 200.0,
        },
        10200001: {
            Web3.to_checksum_address("0x1234567890123456789012345678901234567890"): 101.0,
            Web3.to_checksum_address("0x2345678901234567890123456789012345678901"): 201.0,
        },
    }

    with_cached_data_output = example_integration.get_block_balances(
        cached_data=cached_data, blocks=[10200002]
    )
    print("With cached data (only fetching block 10200002):")
    print(with_cached_data_output)
    print()
    
    print("Felix USDe Integration test completed!")