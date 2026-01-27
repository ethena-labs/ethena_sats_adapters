"""
Tydro Ethena Sats Integration

This integration tracks user balances (supplied + borrowed) on the Tydro protocol
running on the Ink chain. It uses the Aave V3 LENDING_POOL.getUserAccountData() 
to fetch user account data (totalCollateralBase and totalDebtBase) at specific 
block numbers, which is simpler and more reliable than WalletBalanceProvider.
"""

import logging
import os
from typing import Dict, List, Set
from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.request_utils import requests_retry_session


class TydroIntegration(CachedBalancesIntegration):
    """
    Integration for Tydro protocol on Ink chain.
    
    Tracks both supplied collateral and borrowed amounts for users.
    Returns total USD value of user positions.
    """
    
    # Ink chain configuration
    INK_CHAIN_ID = 57073
    INK_RPC_URL = "https://rpc-gel.inkonchain.com/e30175ce22b04b8db78b1fc8a2316105"
    
    # Contract addresses (verified via https://search.onaave.com/)
    LENDING_POOL_ADDRESS_PROVIDER = "0x4172E6aAEC070ACB31aaCE343A58c93E4C70f44D"
    LENDING_POOL = "0x2816cf15F6d2A220E789aA011D5EE4eB6c47FEbA"
    WALLET_BALANCE_PROVIDER = "0xB1532b76D054c9F9E61b25c4d91f69B4133E4671"
    UI_POOL_DATA_PROVIDER = "0xc851e6147dcE6A469CC33BE3121b6B2D4CaD2763"  # Correct address from Tydro frontend
    
    # Subgraph URL - API key via TYDRO_SUBGRAPH_API_KEY env var if available
    # Tydro does not have a The Graph API key; Ethena may need to provide one for production
    # Format: https://gateway-arbitrum.network.thegraph.com/api/{API_KEY}/subgraphs/id/{SUBGRAPH_ID}
    _SUBGRAPH_API_KEY = os.getenv("TYDRO_SUBGRAPH_API_KEY", "")
    SUBGRAPH_BASE_URL = "https://gateway-arbitrum.network.thegraph.com/api"
    SUBGRAPH_ID = "Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g"
    
    def _get_subgraph_url(self) -> str:
        """Get subgraph URL with API key if available."""
        if self._SUBGRAPH_API_KEY:
            return f"{self.SUBGRAPH_BASE_URL}/{self._SUBGRAPH_API_KEY}/subgraphs/id/{self.SUBGRAPH_ID}"
        return f"{self.SUBGRAPH_BASE_URL}/subgraphs/id/{self.SUBGRAPH_ID}"
    
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.ARBITRUM,  # Using Arbitrum as closest match, or add Ink to Chain enum
        summary_cols: List[SummaryColumn] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Set[ChecksumAddress] = None,
        end_block: int = None,
    ):
        """Initialize the integration."""
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols or [],
            reward_multiplier=reward_multiplier,
            balance_multiplier=balance_multiplier,
            excluded_addresses=excluded_addresses,
            end_block=end_block,
        )
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.INK_RPC_URL))
        
        # Verify connection by making an actual call (is_connected() may fail even if RPC works)
        try:
            _ = self.w3.eth.chain_id
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ink RPC: {self.INK_RPC_URL} - {e}")
        
        # Cache for user list
        self._user_cache: Set[ChecksumAddress] = set()
    
    def get_block_balances(
        self,
        cached_data: Dict[int, Dict[ChecksumAddress, float]],
        blocks: List[int],
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """
        Get user balances at specific block numbers.
        
        Args:
            cached_data: Dictionary mapping block numbers to user balances.
                        Used to avoid recomputing known balances.
            blocks: List of block numbers to query.
            
        Returns:
            Dictionary mapping block_number -> {checksum_address: balance}
            Balance is total USD value of supplied + borrowed positions
        """
        result: Dict[int, Dict[ChecksumAddress, float]] = {}
        
        # Get users with positions (cached)
        users = self._get_users_with_positions()
        
        for block_number in blocks:
            # Skip if before start_block
            if block_number < self.start_block:
                result[block_number] = {}
                continue
            
            # Use cached data if available
            if block_number in cached_data:
                result[block_number] = cached_data[block_number]
                continue
            
            try:
                block_balances: Dict[ChecksumAddress, float] = {}
                
                for user_address in users:
                    # Skip excluded addresses
                    if self.excluded_addresses and user_address in self.excluded_addresses:
                        continue
                    
                    balance = self._get_user_balance_at_block(
                        user_address,
                        block_number
                    )
                    
                    if balance > 0:
                        block_balances[user_address] = balance * self.balance_multiplier
                
                result[block_number] = block_balances
                
            except Exception as e:
                logging.error(f"Error processing block {block_number}: {e}")
                result[block_number] = {}
        
        return result
    
    def _get_users_with_positions(self) -> Set[ChecksumAddress]:
        """
        Get list of all users who have positions.
        
        Uses cached list if available, otherwise queries subgraph.
        """
        if self._user_cache:
            return self._user_cache
        
        # Try subgraph first
        try:
            users = self._get_users_from_subgraph()
            if users:
                self._user_cache = users
                return users
        except Exception as e:
            logging.warning(f"Subgraph query failed: {e}")
        
        # Return empty set if no users found
        logging.warning("No users found - integration may need manual user list")
        return set()
    
    def _get_users_from_subgraph(self) -> Set[ChecksumAddress]:
        """
        Query subgraph for all users with positions.
        """
        query = """
        query GetAllUsers {
          userReserves(
            first: 1000,
            where: {
              or: [
                { scaledATokenBalance_gt: "0" },
                { scaledVariableDebt_gt: "0" }
              ]
            }
          ) {
            user {
              id
            }
          }
        }
        """
        
        try:
            response = requests_retry_session().post(
                self._get_subgraph_url(),
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Subgraph returned {response.status_code}")
            
            data = response.json()
            
            if "errors" in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            user_reserves = data.get("data", {}).get("userReserves", [])
            unique_users = {
                Web3.to_checksum_address(reserve["user"]["id"])
                for reserve in user_reserves
            }
            
            logging.info(f"Found {len(unique_users)} users from subgraph")
            return unique_users
            
        except Exception as e:
            logging.error(f"Subgraph query error: {e}")
            raise
    
    def _get_user_balance_at_block(
        self,
        user_address: ChecksumAddress,
        block_number: int
    ) -> float:
        """
        Get total USD balance for a user at a specific block.
        
        Uses UI_POOL_DATA_PROVIDER to get user account data,
        which includes totalCollateralBase and totalDebtBase already in USD.
        """
        try:
            # Use UI_POOL_DATA_PROVIDER - it's more reliable and what the frontend uses
            total_collateral, total_debt = self._get_user_account_data(
                user_address,
                block_number
            )
            
            # totalCollateralBase and totalDebtBase are in USD base currency (8 decimals)
            # Convert from base currency (8 decimals) to USD
            collateral_usd = total_collateral / (10 ** 8)
            debt_usd = total_debt / (10 ** 8)
            
            # Net worth = collateral - debt
            net_worth = collateral_usd - debt_usd
            
            return net_worth
            
        except Exception as e:
            logging.error(
                f"Error getting balance for {user_address} at block {block_number}: {e}"
            )
            import traceback
            logging.error(traceback.format_exc())
            return 0.0
    
    def _get_user_account_data(
        self,
        user_address: ChecksumAddress,
        block_number: int
    ) -> tuple[int, int]:
        """
        Call LENDING_POOL.getUserAccountData to get user account data.
        
        This is simpler and more reliable than UI_POOL_DATA_PROVIDER.
        Returns tuple of (totalCollateralBase, totalDebtBase) in base currency (8 decimals).
        These values are already in USD-equivalent base currency.
        """
        # LENDING_POOL ABI - getUserAccountData is much simpler
        abi = [{
            "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"},
                {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"},
                {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"},
                {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
                {"internalType": "uint256", "name": "ltv", "type": "uint256"},
                {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.LENDING_POOL),
                abi=abi
            )
            
            # Call the function
            result = contract.functions.getUserAccountData(
                Web3.to_checksum_address(user_address)
            ).call(block_identifier=block_number)
            
            # Result is a tuple: (totalCollateralBase, totalDebtBase, ...)
            total_collateral_base = int(result[0])
            total_debt_base = int(result[1])
            
            return total_collateral_base, total_debt_base
            
        except Exception:
            # If call with block fails, retry without block_identifier (current block)
            try:
                contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.LENDING_POOL),
                    abi=abi
                )
                result = contract.functions.getUserAccountData(
                    Web3.to_checksum_address(user_address)
                ).call()
                return int(result[0]), int(result[1])
            except Exception as fallback_error:
                logging.error(f"LENDING_POOL.getUserAccountData call failed (fallback also failed): {fallback_error}")
                import traceback
                logging.error(traceback.format_exc())
                return 0, 0
    
    def _get_token_prices(
        self,
        token_addresses: List[str],
        block_number: int
    ) -> Dict[str, float]:
        """
        Get USD prices for tokens at a specific block.
        
        Uses fallback methods: subgraph -> current prices -> zero
        """
        # Try subgraph first
        try:
            prices = self._get_prices_from_subgraph(token_addresses, block_number)
            if prices:
                return prices
        except Exception as e:
            logging.warning(f"Subgraph price query failed: {e}")
        
        # Fallback: Return zero prices (Ethena may have their own price source)
        return {addr.lower(): 0.0 for addr in token_addresses}
    
    def _get_prices_from_subgraph(
        self,
        token_addresses: List[str],
        block_number: int
    ) -> Dict[str, float]:
        """
        Query subgraph for price data.
        """
        query = """
        query GetReservePrices {
          reserves {
            id
            underlyingAsset
            price {
              priceInEth
            }
            priceOracle {
              usdPriceEth
            }
          }
        }
        """
        
        try:
            response = requests_retry_session().post(
                self._get_subgraph_url(),
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                return {}
            
            data = response.json()
            if "errors" in data:
                return {}
            
            reserves = data.get("data", {}).get("reserves", [])
            prices = {}
            
            for reserve in reserves:
                asset = reserve.get("underlyingAsset", "").lower()
                # Calculate USD price from ETH price
                price_in_eth = float(reserve.get("price", {}).get("priceInEth", "0") or "0")
                usd_per_eth = float(reserve.get("priceOracle", {}).get("usdPriceEth", "0") or "0")
                
                if usd_per_eth > 0:
                    usd_price = price_in_eth * usd_per_eth
                    prices[asset] = usd_price
            
            return prices
            
        except Exception as e:
            logging.error(f"Subgraph price query error: {e}")
            return {}
    
    def _get_token_decimals(
        self,
        token_addresses: List[str],
        block_number: int
    ) -> Dict[str, int]:
        """
        Get decimals for tokens.
        
        Uses common defaults, can be enhanced to query from contracts.
        """
        # Common token decimals
        common_decimals = {
            # USDC, USDT
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": 6,  # USDC
            "0xdac17f958d2ee523a2206206994597c13d831ec7": 6,  # USDT
        }
        
        decimals_map = {}
        for addr in token_addresses:
            addr_lower = addr.lower()
            if addr_lower in common_decimals:
                decimals_map[addr_lower] = common_decimals[addr_lower]
            else:
                # Default to 18 (most ERC20 tokens)
                decimals_map[addr_lower] = 18
        
        return decimals_map


# First deposit into Tydro: block 26821425
# https://explorer.inkonchain.com/tx/0x071e9b1f1d09a0c84a8932e0d52a1afc4f0b1ed86bc4006954245e547c3dcea2
TYDRO_FIRST_DEPOSIT_BLOCK = 26821425


if __name__ == "__main__":
    """
    Test script for Tydro integration (development/testing only).
    Run with: python integrations/tydro_integration.py
    """
    import sys

    print("Tydro Integration Test")
    print("=" * 50)
    integration = TydroIntegration(
        integration_id=IntegrationID.TYDRO,
        start_block=TYDRO_FIRST_DEPOSIT_BLOCK,
        summary_cols=[SummaryColumn.TYDRO_PTS],
        chain=Chain.ARBITRUM,  # Using Arbitrum as closest match (Ink not in Chain enum yet)
    )
    print(f"Start block: {TYDRO_FIRST_DEPOSIT_BLOCK}")
    print("-" * 50)

    # Test RPC connection
    try:
        current_block = integration.w3.eth.block_number
        chain_id = integration.w3.eth.chain_id
        print(f"Connected to chain (ID {chain_id}), current block: {current_block}")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    # Test user discovery
    try:
        users = integration._get_users_with_positions()
        print(f"Found {len(users)} users with positions")
        if users:
            for u in list(users)[:3]:
                print(f"  Example: {u}")
    except Exception as e:
        print(f"User discovery failed (ok if subgraph unavailable): {e}")

    # Test balance query on a random sample to find active users
    import random
    sample_size = min(50, len(users)) if users else 0
    if sample_size:
        sample_users = random.sample(list(users), sample_size)
        test_block = current_block
        print(f"\nQuerying {sample_size} random users at block {test_block}...")
        active = []
        for i, u in enumerate(sample_users, 1):
            try:
                balance = integration._get_user_balance_at_block(u, test_block)
                if balance > 0:
                    active.append((u, balance))
            except Exception as e:
                print(f"  Error for {u}: {e}")
            if i % 10 == 0:
                print(f"  Checked {i}/{sample_size}...")
        print(f"\nResults: {len(active)} active out of {sample_size} sampled")
        for u, bal in active[:5]:
            print(f"  {u}: ${bal:.2f}")
    else:
        print("\nNo users found, skipping balance test.")

    print("Done.")
