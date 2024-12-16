import math
from typing import Dict, Set

from eth_typing import ChecksumAddress
from web3 import Web3

from utils.web3_utils import call_with_retry, fetch_events_logs_with_retry
from utils.web3_utils import w3_mantle

from constants.agni import (
    usde_cmeth_025,
    usde_usdt_001,
    susde_usde_005,
    usdc_usde_001,

    usde_cmeth_025_contract,
    usde_usdt_001_contract,
    susde_usde_005_contract,
    usdc_usde_001_contract,
    position_manager_contract,
    MAX_TICK_RANGE,
    START_BLOCK,
    compute_pool_address, usde_address
)


def get_agni_pool_info_list(
        pools,
        start=START_BLOCK,
        end=w3_mantle.eth.get_block_number(),
) -> Dict[ChecksumAddress, Dict[ChecksumAddress, Set[int]]]:
    pools = {Web3.to_checksum_address(pool) for pool in pools}
    pool_info_list: Dict[ChecksumAddress, Dict[ChecksumAddress, Set[int]]] = {}

    for pool in pools:
        pool_info_list[pool] = {}

    while start < end:
        to_block = start + 1900
        if to_block > end:
            to_block = end

        deposits = fetch_events_logs_with_retry(
            "Agni users",
            position_manager_contract.events.IncreaseLiquidity(),
            start,
            to_block,
        )
        print(start, to_block, len(deposits), "getting deposits for agni")
        for deposit in deposits:
            try:
                token_id = deposit["args"]["tokenId"]
                position = position_manager_contract.functions.positions(token_id).call(
                    block_identifier=end
                )
                pool_address = Web3.to_checksum_address(compute_pool_address(position[2], position[3], position[4]))
                if pool_address not in pools:
                    continue
                owner = position_manager_contract.functions.ownerOf(token_id).call(
                    block_identifier=end
                )
                owner = Web3.to_checksum_address(owner)
                users = pool_info_list[pool_address]
                if owner not in users:
                    users[owner] = {deposit["args"]["tokenId"]}
                else:
                    users[owner].add(deposit["args"]["tokenId"])
            except Exception:
                # nft does not exist at current block
                continue

        if to_block == end:
            break

        start += 1900
    return pool_info_list


def get_pool_price(
        contract, block=w3_mantle.eth.get_block_number() - 100
):  # assumes both tokens are using same number of decimals
    slot0 = call_with_retry(contract.functions.slot0(), block)
    return int(slot0[0])


def get_pool_tick(contract, block=w3_mantle.eth.get_block_number() - 100):
    return math.log(
        ((call_with_retry(contract.functions.slot0(), block)[0]) / (2 ** 96)) ** 2
    ) / math.log(1.0001)


def get_agnis_position_balance(token_id, block, tick, sqrt_ratio_x96):
    try:
        [_, _, token0, token1, _, tick_lower, tick_upper, liquidity, _, _, _, _] = (
            call_with_retry(position_manager_contract.functions.positions(token_id), block)
        )
    except Exception:
        print(token_id, "not yet created at", block)
        return [None, None, 0, 0]
    result = calculate_agni_tokens(
        tick, tick_lower, tick_upper, sqrt_ratio_x96, liquidity
    )
    return [token0, token1, result[0], result[1]]


def calculate_agni_tokens(tick, tick_lower, tick_upper, sqrt_ratio_x96, liquidity):
    if liquidity == 0:
        return [0, 0]
    if abs(tick_lower) > MAX_TICK_RANGE or abs(tick_upper) > MAX_TICK_RANGE:
        return [0, 0]
    t0 = 0
    t1 = 0
    sqrt_ratio_l = int(math.sqrt(1.0001) ** tick_upper * (2 ** 96))
    sqrt_ratio_u = int(math.sqrt(1.0001) ** tick_lower * (2 ** 96))
    liquidity_96 = liquidity << 96
    if tick_lower < tick < tick_upper:
        t0 = liquidity_96 * abs((sqrt_ratio_l - sqrt_ratio_x96)) / (sqrt_ratio_x96 * sqrt_ratio_l)
        t1 = liquidity * abs(sqrt_ratio_x96 - sqrt_ratio_u) / (2 ** 96)
    elif tick >= tick_upper:
        t1 = liquidity * abs(sqrt_ratio_u - sqrt_ratio_l) / (2 ** 96)
    else:
        t0 = liquidity_96 * abs(sqrt_ratio_u - sqrt_ratio_l) / (sqrt_ratio_u * sqrt_ratio_l)
    return [abs(t0 / 10 ** 18), abs(t1 / 10 ** 18)]


def get_agni_all_user_balance(pool: ChecksumAddress, users: Dict[ChecksumAddress, Set[int]],
                              block=w3_mantle.eth.get_block_number()):
    try:
        if block < START_BLOCK:
            return {}
        if pool == Web3.to_checksum_address(usde_cmeth_025):
            contract = usde_cmeth_025_contract
        elif pool == Web3.to_checksum_address(usde_usdt_001):
            contract = usde_usdt_001_contract
        elif pool == Web3.to_checksum_address(susde_usde_005):
            contract = susde_usde_005_contract
        elif pool == Web3.to_checksum_address(usdc_usde_001):
            contract = usdc_usde_001_contract
        else:
            raise Exception("Unknown pool")

        print(users)
        all_user_total_balances = {}

        if len(users) == 0:
            return all_user_total_balances

        sqrt_ratio_x96 = get_pool_price(contract, block)
        tick = get_pool_tick(contract, block)
        print(sqrt_ratio_x96, tick)

        for user in users:
            token_ids = users[user]
            usde = 0
            for token_id in token_ids:
                [token0, token1, t0, t1] = get_agnis_position_balance(token_id, block, tick, sqrt_ratio_x96)
                if token0 is None or token1 is None:
                    continue
                if token0 == usde_address:
                    usde += t0
                elif token1 == usde_address:
                    usde += t1
            all_user_total_balances[user] = round(usde, 2)
            print(user, usde, len(token_ids))
        return all_user_total_balances
    except Exception :
        return {}


if __name__ == "__main__":
    pool_infos = get_agni_pool_info_list({usde_cmeth_025}, 72671947, 72671949)
    print(pool_infos)

    user_balance = get_agni_all_user_balance(usde_cmeth_025,pool_infos[usde_cmeth_025],72671947)
    print(user_balance)
