import logging
from typing import Dict, List, Optional, Set

from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.nhype import NHYPE_CONTRACT, NHYPE_CONTRACT_ADDRESS
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import W3_BY_CHAIN, call_with_retry, fetch_events_logs_with_retry


class NhypeIntegration(CachedBalancesIntegration):
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
        self.w3 = W3_BY_CHAIN[Chain.HYPEREVM]["w3"]
        self._participants_cache: Optional[Set[ChecksumAddress]] = None

    def get_participants(self, blocks: Optional[List[int]] = None) -> Set[ChecksumAddress]:
        """Get all participants who have ever held nHYPE tokens."""
        if self._participants_cache is not None:
            return self._participants_cache

        logging.info("[nHYPE integration] Fetching all participants from Transfer events")
        all_users: Set[ChecksumAddress] = set()

        # Get current block or use the max block from the list
        if blocks:
            end_block = max(blocks)
        else:
            end_block = self.w3.eth.get_block_number()

        start = self.start_block
        batch_size = 500

        while start <= end_block:
            current_batch_end = min(start + batch_size - 1, end_block)
            logging.info(f"[nHYPE integration] Fetching Transfer events from block {start} to {current_batch_end}")

            try:
                transfers = fetch_events_logs_with_retry(
                    f"nHYPE Token {NHYPE_CONTRACT_ADDRESS}",
                    NHYPE_CONTRACT.events.Transfer(),
                    start,
                    current_batch_end,
                )

                for transfer in transfers:
                    from_address = transfer["args"]["from"]
                    to_address = transfer["args"]["to"]

                    # Skip zero address
                    zero_addr = "0x0000000000000000000000000000000000000000"
                    if from_address != zero_addr:
                        all_users.add(Web3.to_checksum_address(from_address))
                    if to_address != zero_addr:
                        all_users.add(Web3.to_checksum_address(to_address))

                logging.info(f"[nHYPE integration] Found {len(transfers)} transfers in batch")

            except Exception as e:
                logging.error(f"[nHYPE integration] Error fetching events for blocks {start}-{current_batch_end}: {e}")

            start = current_batch_end + 1

        # Exclude addresses if specified
        if self.excluded_addresses:
            all_users = all_users - self.excluded_addresses

        self._participants_cache = all_users
        logging.info(f"[nHYPE integration] Found {len(all_users)} unique participants")
        return all_users

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Get user balances for specified blocks, using cached data when available.

        Args:
            cached_data (Dict[int, Dict[ChecksumAddress, float]]): Dictionary mapping block numbers
                to user balances at that block. Used to avoid recomputing known balances.
                The inner dictionary maps user addresses to their nHYPE balance.
            blocks (List[int]): List of block numbers to get balances for.

        Returns:
            Dict[int, Dict[ChecksumAddress, float]]: Dictionary mapping block numbers to user balances,
                where each inner dictionary maps user addresses to their nHYPE balance
                at that block.
        """
        logging.info(f"[nHYPE integration] Getting block balances for {len(blocks)} blocks")

        # Initialize result dictionary
        result_data: Dict[int, Dict[ChecksumAddress, float]] = {}

        # Get all participants up to the max block we're querying
        participants = self.get_participants(blocks)

        # Process each block
        for block in blocks:
            # Skip blocks before the start block
            if block < self.start_block:
                result_data[block] = {}
                continue

            # Use cached data if available
            if block in cached_data and cached_data[block]:
                logging.info(f"[nHYPE integration] Using cached data for block {block}")
                result_data[block] = cached_data[block]
                continue

            # Get fresh data for this block
            logging.info(
                f"[nHYPE integration] Fetching balances for block {block} with {len(participants)} participants"
            )
            block_balances: Dict[ChecksumAddress, float] = {}

            for user in participants:
                try:
                    # Get the nHYPE balance for this user at this block
                    balance_wei = call_with_retry(NHYPE_CONTRACT.functions.balanceOf(user), block)

                    # Convert from wei to token units (18 decimals)
                    balance = float(balance_wei) / 10**18

                    # Only include non-zero balances
                    if balance > 0:
                        block_balances[user] = balance

                except Exception as e:
                    logging.error(f"[nHYPE integration] Error getting balance for user {user} at block {block}: {e}")

            result_data[block] = block_balances
            logging.info(
                f"[nHYPE integration] Found {len(block_balances)} users with non-zero balances at block {block}"
            )

        return result_data


if __name__ == "__main__":
    """
    Test script for the nHYPE integration.
    This is for development/testing only and not used when the integration is run as part of the Ethena system.
    """
    # Create example integration
    example_integration = NhypeIntegration(
        integration_id=IntegrationID.NHYPE_LST,
        start_block=19500000,
        summary_cols=[SummaryColumn.NHYPE_LST_PTS],
        chain=Chain.HYPEREVM,
        reward_multiplier=20,  # Default multiplier
        excluded_addresses={Web3.to_checksum_address("0x0000000000000000000000000000000000000000")},
    )

    # Test without cached data
    print("Testing nHYPE Integration")
    print("=" * 50)

    # Use recent blocks for testing
    test_blocks = [19500100, 19500101, 19500102]
    without_cached_data_output = example_integration.get_block_balances(cached_data={}, blocks=test_blocks)
    print("Without cached data:")
    print(without_cached_data_output)
    print()

    # Test with cached data
    cached_data = {
        19500100: {
            Web3.to_checksum_address("0x1234567890123456789012345678901234567890"): 100.0,
            Web3.to_checksum_address("0x2345678901234567890123456789012345678901"): 200.0,
        },
        19500101: {
            Web3.to_checksum_address("0x1234567890123456789012345678901234567890"): 101.0,
            Web3.to_checksum_address("0x2345678901234567890123456789012345678901"): 201.0,
        },
    }

    with_cached_data_output = example_integration.get_block_balances(cached_data=cached_data, blocks=[19500102])
    print("With cached data (only fetching block 19500102):")
    print(with_cached_data_output)
    print()

    print("nHYPE Integration test completed!")
