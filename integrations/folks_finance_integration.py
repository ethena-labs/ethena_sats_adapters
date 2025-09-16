from typing import Callable, Dict, List, Optional, Set, Tuple
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from eth_typing import ChecksumAddress
from web3 import Web3
from utils.web3_utils import (
    fetch_events_logs_with_retry,
)
from constants.folks_finance import (
    LOAN_MANAGER_CONTRACT,
    TOKEN_TO_POOL_IDS,
    LOAN_TO_ADDRESSES_INDEXER_URL,
    STARTING_BLOCKS,
)
import requests


def extract_loan_event_data(event) -> Dict:
    """Extract loan data from blockchain event."""
    return {
        "loanId": Web3.to_hex(event.args.loanId),
        "amount": event.args.amount,
        "blockNumber": event.blockNumber,
    }


class FolksFinanceIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.AVALANCHE,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block: Optional[int] = None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func: Optional[Callable[[int, str], int]] = None,
        batch_size: int = 2000,
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
        self.pool_id = TOKEN_TO_POOL_IDS[integration_id.token]
        self.batch_size = batch_size  # Number of blocks to process in each batch

    def fetch_loans_from_api(self, to_block: int) -> Dict[str, ChecksumAddress]:
        """Fetch loan ID to address mappings from the API with pagination.

        Args:
            to_block (int): The maximum block number to filter loans up to

        Returns:
            Dict[str, ChecksumAddress]: Dictionary mapping loan ID to user address

        Raises:
            Exception: If API request fails after retries
        """
        loans_mapping = {}
        next_cursor = None

        while True:
            params = {"poolId": self.pool_id, "toBlock": to_block}

            if next_cursor:
                params["next"] = next_cursor

            response = requests.get(
                LOAN_TO_ADDRESSES_INDEXER_URL, params=params, timeout=5
            )
            response.raise_for_status()
            data = response.json()

            # Process loans from this page
            loans = data.get("data", {}).get("loans", [])
            for loan in loans:
                loan_id = loan.get("loanId")
                address = loan.get("address")
                if loan_id and address:
                    checksum_address = Web3.to_checksum_address(address)
                    loans_mapping[loan_id] = checksum_address

            # Check if there's more data
            next_cursor = data.get("next")
            if not next_cursor:
                break

        return loans_mapping

    def _determine_computation_range(
        self, blocks: List[int], cached_data: Dict[int, Dict[ChecksumAddress, float]]
    ) -> Tuple[int, Dict[ChecksumAddress, float], List[int]]:
        """Determine the optimal range for computation based on cached data.

        Args:
            blocks: List of requested block numbers
            cached_data: Previously computed block balances

        Returns:
            Tuple of (start_block, starting_balances, uncached_blocks)
        """
        uncached_blocks = [block for block in blocks if block not in cached_data]

        if not uncached_blocks:
            return 0, {}, []

        min_uncached_block = min(uncached_blocks)
        starting_balances = {}
        start_block = min_uncached_block

        # Find the highest cached block before our computation range
        if cached_data:
            best_cached_block = None
            for cached_block in sorted(cached_data.keys(), reverse=True):
                if cached_block < min_uncached_block:
                    best_cached_block = cached_block
                    break

            if best_cached_block is not None:
                starting_balances = cached_data[best_cached_block].copy()
                start_block = best_cached_block + 1

        return start_block, starting_balances, uncached_blocks

    def _fetch_events_in_range(
        self, start_block: int, end_block: int
    ) -> Tuple[List[Dict], List[Dict]]:
        """Fetch deposit and withdrawal events for a given block range.

        Args:
            start_block: Starting block number (inclusive)
            end_block: Ending block number (inclusive)

        Returns:
            Tuple of (deposits, withdrawals) event lists
        """
        all_deposits = []
        all_withdrawals = []

        current_start = start_block
        while current_start <= end_block:
            current_end = min(current_start + self.batch_size - 1, end_block)

            deposits = list(
                map(
                    extract_loan_event_data,
                    fetch_events_logs_with_retry(
                        "Deposit " + str(self.pool_id),
                        LOAN_MANAGER_CONTRACT.events.Deposit(),
                        from_block=current_start,
                        to_block=current_end,
                        filter={"poolId": self.pool_id},
                    ),
                )
            )

            withdrawals = list(
                map(
                    extract_loan_event_data,
                    fetch_events_logs_with_retry(
                        "Withdraw " + str(self.pool_id),
                        LOAN_MANAGER_CONTRACT.events.Withdraw(),
                        from_block=current_start,
                        to_block=current_end,
                        filter={"poolId": self.pool_id},
                    ),
                )
            )

            all_deposits.extend(deposits)
            all_withdrawals.extend(withdrawals)

            current_start = current_end + 1

        return all_deposits, all_withdrawals

    def _process_events_for_block(
        self,
        block_num: int,
        deposits: List[Dict],
        withdrawals: List[Dict],
        loans_mapping: Dict[str, ChecksumAddress],
        current_balances: Dict[ChecksumAddress, float],
    ) -> None:
        """Process deposit and withdrawal events for a specific block.

        Args:
            block_num: Block number to process
            deposits: List of deposit events
            withdrawals: List of withdrawal events
            loans_mapping: Mapping of loan IDs to addresses
            current_balances: Current balance state (modified in place)
        """
        # Process deposits for this block
        for deposit in [d for d in deposits if d["blockNumber"] == block_num]:
            loan_id = deposit["loanId"]
            amount = deposit["amount"]

            if loan_id in loans_mapping:
                address = loans_mapping[loan_id]
                current_balances[address] = current_balances.get(address, 0) + amount

        # Process withdrawals for this block
        for withdrawal in [w for w in withdrawals if w["blockNumber"] == block_num]:
            loan_id = withdrawal["loanId"]
            amount = withdrawal["amount"]

            if loan_id in loans_mapping:
                address = loans_mapping[loan_id]
                current_balances[address] = max(
                    0, current_balances.get(address, 0) - amount
                )

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Get user balances for specified blocks, using cached data when available.

        This method efficiently computes balances by:
        1. Using cached data when available
        2. Starting computation from the latest cached block
        3. Processing events chronologically to maintain balance persistence
        4. Only fetching data for the minimum required range

        Args:
            cached_data: Previously computed block balances
            blocks: List of block numbers to get balances for

        Returns:
            Dictionary mapping block numbers to user balances
        """
        if not blocks:
            return {}

        blocks = sorted(blocks)
        result = {}

        if min(blocks) < self.start_block:
            return result

        # Add all cached blocks to result
        for block in blocks:
            if block in cached_data:
                result[block] = cached_data[block].copy()

        # Determine what we need to compute
        start_block, starting_balances, uncached_blocks = (
            self._determine_computation_range(blocks, cached_data)
        )

        if not uncached_blocks:
            return result

        max_uncached_block = max(uncached_blocks)

        # Fetch loan mappings and events
        loans_mapping = self.fetch_loans_from_api(max_uncached_block)
        deposits, withdrawals = self._fetch_events_in_range(
            start_block, max_uncached_block
        )

        # Process events chronologically to build cumulative balances
        current_balances = starting_balances.copy()

        for block_num in range(start_block, max_uncached_block + 1):
            self._process_events_for_block(
                block_num, deposits, withdrawals, loans_mapping, current_balances
            )

            # Store balance for requested uncached blocks only
            if block_num in uncached_blocks:
                result[block_num] = current_balances.copy()

        return result


if __name__ == "__main__":
    # Test the integration with example data
    folks_finance_usde_integration = FolksFinanceIntegration(
        integration_id=IntegrationID.FOLKS_FINANCE_USDE,
        start_block=STARTING_BLOCKS[IntegrationID.FOLKS_FINANCE_USDE.token],
        summary_cols=[SummaryColumn.FOLKS_FINANCE_USDE_PTS],
        chain=Chain.AVALANCHE,
        reward_multiplier=20,
        excluded_addresses=set(),
    )

    test_blocks = list(range(68822406, 68824580))
    # Example cached data
    cached_balances = {}

    result = folks_finance_usde_integration.get_block_balances(
        cached_data=cached_balances, blocks=test_blocks
    )
    print(result)

    folks_finance_susde_integration = FolksFinanceIntegration(
        integration_id=IntegrationID.FOLKS_FINANCE_SUSDE,
        start_block=STARTING_BLOCKS[IntegrationID.FOLKS_FINANCE_SUSDE.token],
        summary_cols=[SummaryColumn.FOLKS_FINANCE_SUSDE_PTS],
        chain=Chain.AVALANCHE,
        reward_multiplier=20,
        excluded_addresses=set(),
    )
    test_blocks = list(range(68822406, 68824580))

    result = folks_finance_susde_integration.get_block_balances(
        cached_data=cached_balances, blocks=test_blocks
    )
    print(result)
