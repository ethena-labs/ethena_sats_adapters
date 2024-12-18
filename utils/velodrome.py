import json
from utils.web3_utils import (
    w3_mode,
    fetch_events_logs_with_retry,
    call_with_retry,
)
from web3 import Web3
from constants.velodrome import (
    VELODROME_MODE_SUGAR_ADDRESS,
    PAGE_SIZE,
    VELODROME_MODE_START_BLOCK,
)

with open("abi/velodrome_sugar.json") as f:
    sugar_abi = json.load(f)

with open("abi/velodrome_pool.json") as f:
    pool_abi = json.load(f)

sugar_contract = w3_mode.eth.contract(
    address=Web3.to_checksum_address(VELODROME_MODE_SUGAR_ADDRESS),
    abi=sugar_abi,
)


def fetch_pools(block):
    total_pools = []
    offset = 0

    while True:
        # get all of the current pools
        pools = call_with_retry(
            sugar_contract.functions.all(PAGE_SIZE, offset),
            block,
        )

        total_pools.extend(pools)

        if len(pools) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    return total_pools


def fetch_participants(token):
    latest_block = w3_mode.eth.get_block_number()
    all_pools = fetch_pools(latest_block)
    pool_addresses = []
    participants = set()

    for pool_data in all_pools:
        if pool_data[7] == token or pool_data[10] == token:
            pool_addresses.append(pool_data[0])

    for pool in pool_addresses:
        pool_contract = w3_mode.eth.contract(address=pool, abi=pool_abi)

        lps = fetch_events_logs_with_retry(
            f"Velodrome Mode users from {VELODROME_MODE_START_BLOCK} to {latest_block}",
            pool_contract.events.Mint(),
            VELODROME_MODE_START_BLOCK,
            latest_block,
        )
        for lp in lps:
            participants.add(lp["args"]["to"])

    return participants


def fetch_balance(user, block, token):
    all_pools = fetch_pools(block)
    total_pools_size = len(all_pools)
    offset = 0
    balance = 0

    while True:
        # get the positions
        positions = call_with_retry(
            sugar_contract.functions.positions(PAGE_SIZE, offset, user),
            block,
        )

        for pos in positions:
            lp_address = pos[1]
            for pool in all_pools:
                if pool[0] == lp_address:
                    if pool[7] == token:
                        balance += pos[4]
                        balance += pos[6]
                    if pool[10] == token:
                        balance += pos[5]
                        balance += pos[7]
                    break

        offset += PAGE_SIZE
        if offset > total_pools_size:
            break
    return balance
