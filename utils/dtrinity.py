import logging
from typing import Dict, List
from decimal import Decimal
from web3 import Web3

from constants.dtrinity import (
    ATOKEN_ABI,
    LENDING_POOL_ABI,
    LENDING_POOL_ADDRESS,
    USDE_ATOKEN_ADDRESS,
    SUSDE_ATOKEN_ADDRESS,
    USDE_GENESIS_BLOCK,
    SUSDE_GENESIS_BLOCK,
    lending_pool_contract,
    usde_atoken_contract,
    susde_atoken_contract
)
from utils.web3_utils import call_with_retry

logger = logging.getLogger(__name__)

def get_lending_pool_contract(web3_instance):
    """
    Create and return the lending pool contract instance.
    """
    return web3_instance.eth.contract(
        address=Web3.to_checksum_address(LENDING_POOL_ADDRESS),
        abi=LENDING_POOL_ABI
    )


def get_atoken_contract(web3_instance, atoken_address):
    """
    Create and return an aToken contract instance.
    """
    return web3_instance.eth.contract(
        address=Web3.to_checksum_address(atoken_address),
        abi=ATOKEN_ABI
    )


def get_active_users(lending_pool, from_block: int, to_block: int) -> List[str]:
    """
    Get a list of users who have had any activity in the given block range.
    This is optimized by looking for relevant events instead of checking all users.
    """
    # Look for deposit/withdrawal events in the lending pool
    deposit_events = lending_pool.events.Supply().get_logs(fromBlock=from_block, toBlock=to_block)
    withdraw_events = lending_pool.events.Withdraw().get_logs(fromBlock=from_block, toBlock=to_block)
    
    # Extract unique user addresses
    users = set()
    for event in deposit_events + withdraw_events:
        users.add(Web3.to_checksum_address(event.args.user))
        
    return list(users)


def get_user_balances(users: List[str], block: int, atoken_contract) -> Dict[str, Decimal]:
    """
    Get user balances for a specific aToken at a specific block.
    """
    balances = {}
    
    for user in users:
        try:
            # Call balanceOf for each user
            balance_raw = call_with_retry(
                atoken_contract.functions.balanceOf(user),
                block
            )
            # Convert to decimal, assuming 18 decimals (standard for aTokens)
            balance = Decimal(balance_raw) / Decimal(10**18)
            balances[user] = balance
        except Exception as e:
            logger.error(f"Error getting balance for {user} at block {block}: {e}")
            
    return balances 