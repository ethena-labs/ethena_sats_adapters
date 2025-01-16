from typing import Dict, Set

from eth_typing import ChecksumAddress
from web3 import Web3

from utils.web3_utils import call_with_retry, fetch_events_logs_with_retry
from utils.web3_utils import w3_base

from constants.infinityPools import (
    MAX_BLOCKS_IN_ONE_CALL,
    START_BLOCK,
    infinityPools_periphery_contract,
    usdc_sUSDe,
    decode_id,
    sUSDe_address,
    infinityPool_contract
)


def get_infinityPools_info_list(
        pools,
        start=START_BLOCK,
        end=w3_base.eth.get_block_number(),
) -> Dict[ChecksumAddress, Dict[ChecksumAddress, Set[int]]]:
    pools = {Web3.to_checksum_address(pool) for pool in pools}
    pool_info_list: Dict[ChecksumAddress, Dict[ChecksumAddress, Set[int]]] = {}

    for pool in pools:
        pool_info_list[pool] = {}

    while start < end:
        to_block = start + MAX_BLOCKS_IN_ONE_CALL
        if to_block > end:
            to_block = end

        liquidity_added_events = fetch_events_logs_with_retry(
            "infinityPools users",
            infinityPools_periphery_contract.events.PeripheryLiquidityAdded(),
            start,
            to_block,
        )
        print(start, to_block, len(liquidity_added_events),
              "getting liquidity_added_events for infinityPools")
        for liquidity_added_event in liquidity_added_events:
            try:
                lpNum = liquidity_added_event["args"]["lpNum"]
                pool_address = liquidity_added_event["args"]["pool"]
                # print(pool_address in pools)
                token_id = infinityPools_periphery_contract.functions.encodeId(
                    0, pool_address, lpNum).call()
                # print("lpNum", lpNum)
                if pool_address not in pools:
                    continue
                owner = liquidity_added_event["args"]["user"]
                owner = Web3.to_checksum_address(owner)
                users = pool_info_list[pool_address]
                if owner not in users:
                    users[owner] = {token_id}
                else:
                    users[owner].add(token_id)
            except Exception:
                # nft does not exist at current block
                continue

        if to_block == end:
            break

        start += MAX_BLOCKS_IN_ONE_CALL
    return pool_info_list


def get_infinityPools_position_balance(token_id, block):
    (_, pool_address, lpNum) = decode_id(token_id)
    infinityPool_contract.address = pool_address
    try:
        [_, token0, token1, _, _, _, locked_amount0, locked_amount1, _, _,
            _, _, _] = call_with_retry(infinityPool_contract.functions.getLiquidityPosition(lpNum), block)
        return [Web3.to_checksum_address(token0), Web3.to_checksum_address(token1), locked_amount0, locked_amount1]
    except Exception:
        print(token_id, "not yet created at", block)
        return [None, None, 0, 0]


def get_infinityPool_all_user_balance(users: Dict[ChecksumAddress, Set[int]],
                                      block=w3_base.eth.get_block_number()) -> Dict[ChecksumAddress, float]:
    try:
        if block < START_BLOCK:
            return {}

        # print("users", users)
        all_user_total_balances: Dict[ChecksumAddress, float] = {}

        if len(users) == 0:
            return all_user_total_balances

        for user in users:
            token_ids = users[user]
            total_sUsde_amount = 0  # per user
            for token_id in token_ids:
                [token0, token1, t0, t1] = get_infinityPools_position_balance(
                    token_id, block)
                # print("amounts", t0, t1)
                if token0 is None or token1 is None:
                    continue
                if token0 == sUSDe_address:
                    total_sUsde_amount += t0
                elif token1 == sUSDe_address:
                    total_sUsde_amount += t1
            all_user_total_balances[user] = round(total_sUsde_amount, 2)
            print(user, total_sUsde_amount, len(token_ids))
        return all_user_total_balances
    except Exception:
        return {}


if __name__ == "__main__":
    pool_infos = get_infinityPools_info_list(
        {usdc_sUSDe}, START_BLOCK, 25037239)
    print(pool_infos)

    # print(get_infinityPools_position_balance(
    #     247501292629419575271898969527583021281002773205275782087105512447577948160, 24813472))

    user_balance = get_infinityPool_all_user_balance(
        pool_infos[usdc_sUSDe], 25037239)
    print(user_balance)
