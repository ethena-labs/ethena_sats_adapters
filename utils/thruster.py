import math
from typing import Dict, Optional, Set

from eth_typing import ChecksumAddress
from web3 import Web3

from utils.web3_utils import (
    call_with_retry,
    multicall_by_address,
    MULTICALL_ADDRESS_BY_CHAIN,
    w3_blast,
    fetch_events_logs_with_retry,
)
from constants.thruster import (
    MAX_TICK_RANGE,
    JUICE_TOKEN_ID,
    HYPERLOCK_DEPOSIT_ADDRESS,
    PARTICLE_LEVERAGED_POOL_ADDRESS,
)
from constants.thruster import thruster_nfp_contract, thruster_usde_pool_contract
from constants.chains import Chain

# Pagination size for fetching events
PAGINATION_SIZE = 2000


def get_thruster_users(
    pool,
    start=4025647,
    end=None,
) -> Dict[ChecksumAddress, Set[int]]:
    """
    Get users of Thruster pools based on events fetching.

    Args:
        pool: The pool address to check
        start: Starting block number
        end: Ending block number (defaults to latest block)

    Returns:
        Dictionary mapping users to their token IDs
    """
    if end is None:
        end = w3_blast.eth.get_block_number()

    users: Dict[ChecksumAddress, Set[int]] = {}

    # Prepare multicall for batch owner queries
    ownerOf_calls = []
    token_ids = []

    while start < end:
        to_block = start + PAGINATION_SIZE
        deposits = fetch_events_logs_with_retry(
            "Thruster users",
            thruster_nfp_contract.events.IncreaseLiquidity(),
            start,
            to_block,
        )
        deposits_list = list(deposits)
        print(start, to_block, len(deposits_list), "getting deposits for thruster")

        for deposit in deposits_list:
            if deposit["args"]["pool"] == pool:
                token_id = deposit["args"]["tokenId"]

                # Exclude the juice token position as we will reward this with their API
                if token_id == JUICE_TOKEN_ID:
                    continue

                # Add this call to our multicall batch
                ownerOf_calls.append(
                    (
                        thruster_nfp_contract,
                        thruster_nfp_contract.functions.ownerOf.fn_name,
                        [token_id],
                    )
                )
                token_ids.append(token_id)

        start += PAGINATION_SIZE

    # Execute multicall for all token ownerships
    if ownerOf_calls:
        multicall_results = multicall_by_address(
            wb3=w3_blast,
            multical_address=MULTICALL_ADDRESS_BY_CHAIN[Chain.BLAST],
            calls=ownerOf_calls,
            block_identifier=end,
        )

        # Process results
        for token_id, result in zip(token_ids, multicall_results):
            try:
                owner = Web3.to_checksum_address(result[0])
            except Exception:
                # nfp does not exist at current block
                continue

            # Exclude the hyperlock deposit address as it's the owner of the deposited positions
            # this will be handled at the Hyperlock integration
            if owner == HYPERLOCK_DEPOSIT_ADDRESS:
                continue

            if owner == PARTICLE_LEVERAGED_POOL_ADDRESS:
                continue

            if owner not in users:
                users[owner] = {token_id}
            else:
                users[owner].add(token_id)

    return users


def get_pool_price(
    contract, block=None
):  # assumes both tokens are using same number of decimals
    if block is None:
        block = w3_blast.eth.get_block_number() - 100
    return (int(call_with_retry(contract.functions.slot0(), block)[0]) / (2**96)) ** 2


def get_pool_tick(contract, block=None):
    if block is None:
        block = w3_blast.eth.get_block_number() - 100
    return math.log(
        ((call_with_retry(contract.functions.slot0(), block)[0]) / (2**96)) ** 2
    ) / math.log(1.0001)


def get_thrusters_position_balance(token_id, block, tick, sqrt_price):
    try:
        [_, _, _, _, _, tick_lower, tick_upper, liquidity, _, _, _, _] = (
            call_with_retry(thruster_nfp_contract.functions.positions(token_id), block)
        )
    except Exception:
        print(f"token {token_id} not yet created at block {block}")
        return [0, 0]
    return calculate_thruster_tokens(
        tick, tick_lower, tick_upper, sqrt_price, liquidity
    )


def calculate_thruster_tokens(tick, tick_lower, tick_upper, sqrt_price, liquidity):
    if liquidity == 0:
        return [0, 0]
    if abs(tick_lower) > MAX_TICK_RANGE or abs(tick_upper) > MAX_TICK_RANGE:
        return [0, 0]
    t0 = 0
    t1 = 0
    sqrt_ratio_l = math.sqrt(1.0001**tick_lower)
    sqrt_ratio_u = math.sqrt(1.0001**tick_upper)
    if tick_lower < tick < tick_upper:
        t0 = liquidity * (sqrt_ratio_u - sqrt_price) / (sqrt_price * sqrt_ratio_u)
        t1 = liquidity * (sqrt_price - sqrt_ratio_l)
    elif tick >= tick_upper:
        t1 = liquidity * (sqrt_ratio_u - sqrt_ratio_l)
    else:
        t0 = liquidity * (sqrt_ratio_u - sqrt_ratio_l) / (sqrt_ratio_u * sqrt_ratio_l)
    return [abs(t0 / 10**18), abs(t1 / 10**18)]


def get_thruster_all_user_balance(pool, block: Optional[int] = None):
    if block is None:
        block = w3_blast.eth.get_block_number() - 100
    if block < 4065496:
        return {}

    contract = thruster_usde_pool_contract
    sqrt_price = math.sqrt(get_pool_price(contract, block))
    tick = get_pool_tick(contract, block)
    users = get_thruster_users(pool, block)
    all_user_total_balances = {}

    for user in users:
        token_ids = users[user]
        user_t0_balances = 0
        user_t1_balances = 0
        for token_id in token_ids:
            [t0, t1] = get_thrusters_position_balance(token_id, block, tick, sqrt_price)
            user_t0_balances += t0
            user_t1_balances += t1
        all_user_total_balances[user] = round(user_t0_balances + user_t1_balances, 2)
    return all_user_total_balances
