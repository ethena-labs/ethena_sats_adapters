import requests
from typing import Callable, Dict, List, Optional, Set, Tuple
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress
from collections import defaultdict
import logging

# Set up logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeswapIntegration(CachedBalancesIntegration):
    """
    Enhanced Timeswap integration with robust transaction tracking and debugging capabilities.
    
    This integration handles all known Timeswap transaction types and provides detailed
    logging for tracking user position changes over time.
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
        debug_mode: bool = False,
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
        
        self.api_url = "https://timeswap-pool-details.vercel.app/api/usde-pool-details"
        self.debug_mode = debug_mode
        
        self.seen_transaction_types = set()
        self.transaction_stats = defaultdict(int)

    def _normalize_address(self, address: str) -> ChecksumAddress:
        """Normalize address to checksum format."""
        return Web3.to_checksum_address(address)

    def _normalize_amount(self, amount_str: Optional[str]) -> float:
        """Convert amount string to float, handling None and scientific notation."""
        if not amount_str or amount_str == "0":
            return 0.0
        try:
            return float(amount_str)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse amount: {amount_str}")
            return 0.0

    def _to_human_readable(self, wei_amount: float, decimals: int = 18) -> float:
        """Convert wei amount to human-readable format."""
        return wei_amount / (10 ** decimals)

    def _log_transaction(self, address: str, tx_type: str, amount: float, pool_id: str, 
                        balance_before: float, balance_after: float) -> None:
        """Log transaction details for debugging."""
        if self.debug_mode:
            logger.info(
                f"TX: {address[:10]}... | {tx_type} | "
                f"Amount: {self._to_human_readable(amount):.2f} USDe | "
                f"Pool: {pool_id[:8]}... | "
                f"Balance: {self._to_human_readable(balance_before):.2f} → "
                f"{self._to_human_readable(balance_after):.2f} USDe"
            )

    def _process_lending_transaction(self, tx: Dict, user_positions: Dict) -> None:
        """Process a lending transaction (LendGivenPrincipal)."""
        address = self._normalize_address(tx["txn_from"])
        pool_id = tx.get("pool_id", "default")
        amount = self._normalize_amount(tx.get("token1_amount_lent"))
        
        if amount > 0:
            balance_before = user_positions[address][pool_id]
            user_positions[address][pool_id] += amount
            balance_after = user_positions[address][pool_id]
            
            self._log_transaction(address, "LEND", amount, pool_id, balance_before, balance_after)

    def _process_close_lending_transaction(self, tx: Dict, user_positions: Dict) -> None:
        """Process a close lending transaction (CloseLendGivenPosition)."""
        address = self._normalize_address(tx["txn_from"])
        pool_id = tx.get("pool_id", "default")
        amount = self._normalize_amount(tx.get("closelend_token1_amount_redeemed"))
        
        if amount > 0:
            balance_before = user_positions[address][pool_id]
            user_positions[address][pool_id] = max(0, user_positions[address][pool_id] - amount)
            balance_after = user_positions[address][pool_id]
            
            self._log_transaction(address, "CLOSE_LEND", amount, pool_id, balance_before, balance_after)

    def _process_add_liquidity_transaction(self, tx: Dict, user_positions: Dict) -> None:
        """Process an add liquidity transaction (AddLiquidityGivenPrincipal)."""
        address = self._normalize_address(tx["txn_from"])
        pool_id = tx.get("pool_id", "default")
        amount = self._normalize_amount(tx.get("token1_amount_added"))
        
        if amount > 0:
            balance_before = user_positions[address][pool_id]
            user_positions[address][pool_id] += amount
            balance_after = user_positions[address][pool_id]
            
            self._log_transaction(address, "ADD_LIQ", amount, pool_id, balance_before, balance_after)

    def _process_remove_liquidity_transaction(self, tx: Dict, user_positions: Dict) -> None:
        """Process a remove liquidity transaction (RemoveLiquidityGivenPosition)."""
        address = self._normalize_address(tx["txn_from"])
        pool_id = tx.get("pool_id", "default")
        amount = self._normalize_amount(tx.get("token1_amount_removed"))
        
        if amount > 0:
            balance_before = user_positions[address][pool_id]
            user_positions[address][pool_id] = max(0, user_positions[address][pool_id] - amount)
            balance_after = user_positions[address][pool_id]
            
            self._log_transaction(address, "REMOVE_LIQ", amount, pool_id, balance_before, balance_after)

    def _process_withdraw_transaction(self, tx: Dict, user_positions: Dict) -> None:
        """Process a withdraw transaction (Withdraw)."""
        address = self._normalize_address(tx["txn_from"])
        pool_id = tx.get("pool_id", "default")
        
        balance_before = user_positions[address][pool_id]
        user_positions[address][pool_id] = 0  
        balance_after = user_positions[address][pool_id]
        
        self._log_transaction(address, "WITHDRAW", balance_before, pool_id, balance_before, balance_after)

    def _calculate_user_balances_from_transactions(self, transactions: List[Dict]) -> Dict[ChecksumAddress, float]:
        """
        Calculate current user balances based on transaction history with enhanced tracking.
        
        Args:
            transactions: List of transaction data from API
            
        Returns:
            Dict mapping user addresses to their current lending balances
        """
        user_positions = defaultdict(lambda: defaultdict(float))
        
        # Sort transactions by timestamp to process in chronological order
        transactions.sort(key=lambda x: int(x.get("txn_timestamp", 0)))
        
        # Process each transaction
        for tx in transactions:
            try:
                address = self._normalize_address(tx["txn_from"])
                tx_type = tx["txn_type"]
                
                # Track transaction types and stats
                self.seen_transaction_types.add(tx_type)
                self.transaction_stats[tx_type] += 1
                
                # Skip excluded addresses
                if self.excluded_addresses and address in self.excluded_addresses:
                    continue
                
                # Process different transaction types
                if tx_type == "LendGivenPrincipal":
                    self._process_lending_transaction(tx, user_positions)
                    
                elif tx_type == "CloseLendGivenPosition":
                    self._process_close_lending_transaction(tx, user_positions)
                    
                elif tx_type == "AddLiquidityGivenPrincipal":
                    self._process_add_liquidity_transaction(tx, user_positions)
                    
                elif tx_type == "RemoveLiquidityGivenPosition":
                    self._process_remove_liquidity_transaction(tx, user_positions)
                
                elif tx_type == "Withdraw":
                    self._process_withdraw_transaction(tx, user_positions)
                    
                elif tx_type == "Collect":       
                    if self.debug_mode:
                        logger.info(f"COLLECT: {address[:10]}... in pool {tx.get('pool_id', 'unknown')[:8]}...")
                
                elif tx_type in ["BorrowGivenPrincipal", "BorrowGivenPosition", "CloseBorrowGivenPosition"]:
                    if self.debug_mode:
                        logger.info(f"BORROW_TX: {address[:10]}... - {tx_type}")
                    
                else:
                    logger.warning(f"Unknown transaction type: {tx_type} for user {address}")
                        
            except (ValueError, KeyError, TypeError) as e:
                logger.error(f"Error processing transaction {tx.get('transaction_hash', 'unknown')}: {e}")
                continue
        
        # Calculate final balances
        final_balances = {}
        total_users = 0
        users_with_balance = 0
        
        for address, pools in user_positions.items():
            total_balance = sum(pools.values())
            if total_balance > 0:
                normalized_balance = self._to_human_readable(total_balance)
                if normalized_balance > 1:  # Minimum threshold to avoid dust
                    final_balances[address] = normalized_balance
                    users_with_balance += 1
            total_users += 1
        
        # Log summary statistics
        logger.info(f"Transaction processing complete:")
        logger.info(f"  - Total users processed: {total_users}")
        logger.info(f"  - Users with active balances: {users_with_balance}")
        logger.info(f"  - Transaction types seen: {sorted(self.seen_transaction_types)}")
        
        if self.debug_mode:
            logger.info("Transaction type counts:")
            for tx_type, count in sorted(self.transaction_stats.items()):
                logger.info(f"  - {tx_type}: {count}")
        
        return final_balances

    def debug_user_transactions(self, user_address: str, transactions: List[Dict]) -> List[Dict]:
        """
        Debug helper to trace all transactions for a specific user.
        
        Args:
            user_address: Address to debug
            transactions: All transactions
            
        Returns:
            List of transactions for the specified user
        """
        user_address = self._normalize_address(user_address)
        user_txs = [tx for tx in transactions if self._normalize_address(tx["txn_from"]) == user_address]
        user_txs.sort(key=lambda x: int(x.get("txn_timestamp", 0)))
        
        logger.info(f"=== DEBUG: Transactions for {user_address} ===")
        
        running_balance = 0.0
        for i, tx in enumerate(user_txs):
            tx_type = tx["txn_type"]
            timestamp = tx.get("formatted_datetime", tx.get("txn_timestamp", "unknown"))
            
            # Calculate balance change
            balance_change = 0.0
            if tx_type == "LendGivenPrincipal":
                balance_change = self._normalize_amount(tx.get("token1_amount_lent"))
                running_balance += balance_change
            elif tx_type == "CloseLendGivenPosition":
                balance_change = -self._normalize_amount(tx.get("closelend_token1_amount_redeemed"))
                running_balance = max(0, running_balance + balance_change)
            elif tx_type == "AddLiquidityGivenPrincipal":
                balance_change = self._normalize_amount(tx.get("token1_amount_added"))
                running_balance += balance_change
            elif tx_type == "RemoveLiquidityGivenPosition":
                balance_change = -self._normalize_amount(tx.get("token1_amount_removed"))
                running_balance = max(0, running_balance + balance_change)
            elif tx_type == "Withdraw":
                balance_change = -running_balance
                running_balance = 0
            
            logger.info(
                f"  {i+1:2d}. {timestamp} | {tx_type:25s} | "
                f"Change: {self._to_human_readable(balance_change):>10.2f} | "
                f"Balance: {self._to_human_readable(running_balance):>10.2f} USDe"
            )
        
        logger.info(f"=== Final balance: {self._to_human_readable(running_balance):.2f} USDe ===")
        return user_txs

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Get user balances for specified blocks, using cached data when available."""
        result = {}
        blocks_needing_data = [block for block in blocks if block not in cached_data]
        
        # Add cached data
        for block in blocks:
            if block in cached_data:
                result[block] = cached_data[block]
        
        if not blocks_needing_data:
            return result
        
        try:
            logger.info(f"Fetching Timeswap data for {len(blocks_needing_data)} blocks...")
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success") and data.get("data"):
                block_data = self._calculate_user_balances_from_transactions(data["data"])
                
                # Apply to all blocks needing data
                for block in blocks_needing_data:
                    result[block] = block_data
            else:
                logger.error("Invalid API response")
                for block in blocks_needing_data:
                    result[block] = {}
                    
        except Exception as e:
            logger.error(f"Error fetching/processing Timeswap data: {e}")
            for block in blocks_needing_data:
                result[block] = {}
        
        return result


if __name__ == "__main__":
    # Enable debug mode for testing
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
        debug_mode=True,  # Enable debug logging
    )
    
    print("Testing Enhanced Timeswap Integration...")
    print("=" * 60)
    
    # Fetch data to test with
    try:
        response = requests.get(timeswap_integration.api_url, timeout=30)
        data = response.json()
        
        if data.get("success") and data.get("data"):
            # Debug specific users
            test_users = [
                "0xfB5349E073996c0F8C1B9EC0A001e4F4F24E0550",
                "0xb3b5610C62B4416f2CD4fbE16aA620b86E60adA7"
            ]
            
            for user in test_users:
                print(f"\n=== DEBUGGING USER: {user} ===")
                timeswap_integration.debug_user_transactions(user, data["data"])
            
            # Calculate final balances
            final_balances = timeswap_integration._calculate_user_balances_from_transactions(data["data"])
            
            print(f"\n=== FINAL RESULTS ===")
            for user in test_users:
                user_checksum = Web3.to_checksum_address(user)
                if user_checksum in final_balances:
                    print(f"❌ PROBLEM: {user} has balance: {final_balances[user_checksum]:.2f} USDe")
                else:
                    print(f"✅ CORRECT: {user} has 0 USDe (properly handled)")
        
    except Exception as e:
        print(f"Error during testing: {e}")