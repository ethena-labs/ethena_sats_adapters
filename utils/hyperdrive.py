import os
import json
import itertools
import eth_abi
from decimal import Decimal, getcontext
from tqdm import tqdm
from enum import IntEnum
from dotenv import load_dotenv
from utils.web3_utils import (
    fetch_events_logs_with_retry,
    w3,
)

from constants.hyperdrive import (
    HYPERDRIVE_ABI,
    MORPHO_ABI,
    ERC20_ABI,
)

load_dotenv()

PAGE_SIZE = 1900
getcontext().prec = 100  # Set precision for Decimal calculations

def get_first_contract_block(contract_address):
    # do binary search up to latest block
    latest_block = w3.eth.get_block_number()
    earliest_block = 0
    while earliest_block < latest_block:
        mid_block = (earliest_block + latest_block) // 2
        # print(f"{mid_block=}")
        attempt_to_get_code = w3.eth.get_code(account=contract_address,block_identifier=mid_block)
        if attempt_to_get_code == b'':
            # Contract not yet deployed, continue searching in the later blocks
            earliest_block = mid_block + 1
        else:
            # Contract deployed, continue searching in the earlier blocks
            latest_block = mid_block - 1
    # At this point, earliest_block and latest_block should be the same,
    # and it represents the block where we can first retrieve the contract code.
    assert earliest_block >= latest_block, f"something fucked up since {earliest_block=} isn't greater than or equal to {latest_block=}"
    return earliest_block

def get_hyperdrive_participants(pool, cache: bool = False):
    target_block = w3.eth.get_block_number()
    all_users = all_ids = start_block = None
    if cache and os.path.exists(f"hyperdrive_users_{pool}.json"):
        with open(f"hyperdrive_users_{pool}.json", "r") as f:
            all_users = set(json.load(f))
    else:
        all_users = set()
    if cache and os.path.exists(f"hyperdrive_ids_{pool}.json"):
        with open(f"hyperdrive_ids_{pool}.json", "r") as f:
            all_ids = set(json.load(f))
    else:
        all_ids = set()
    if cache and os.path.exists(f"hyperdrive_latest_block_{pool}.json"):
        with open(f"hyperdrive_latest_block_{pool}.json", "r") as f:
            start_block = json.load(f) + 1
        if start_block >= target_block:
            print(f"Skipping pool {pool} because it's up to date.")
            return all_users, all_ids
    else:
        start_block = get_first_contract_block(pool)
    assert all_users is not None, "error: all_users is None"
    assert all_ids is not None, "error: all_ids is None"
    assert start_block is not None, "error: start_block is None"
    contract = w3.eth.contract(address=pool, abi=HYPERDRIVE_ABI)
    
    total_blocks_to_process = target_block - start_block
    with tqdm(total=total_blocks_to_process, desc="Fetching Hyperdrive events", unit="block") as pbar:
        current_block = start_block
        while current_block < target_block:
            to_block = min(current_block + PAGE_SIZE, target_block)
            transfers = fetch_events_logs_with_retry(
                label=f"Hyperdrive users {pool}",
                contract_event=contract.events.TransferSingle(),
                from_block=current_block,
                to_block=to_block,
                delay=0,
            )
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
                all_ids.add(transfer["args"]["id"])
            # Update the progress bar by the number of blocks processed in this iteration
            blocks_processed = to_block - current_block
            pbar.update(blocks_processed)
            current_block = to_block
    if cache:
        with open(f"hyperdrive_users_{pool}.json", "w") as f:
            json.dump(list(all_users), f)
        with open(f"hyperdrive_ids_{pool}.json", "w") as f:
            json.dump(list(all_ids), f)
        with open(f"hyperdrive_latest_block_{pool}.json", "w") as f:
            json.dump(target_block, f)

    return all_users, all_ids

class HyperdrivePrefix(IntEnum):
    r"""The asset ID is used to encode the trade type in a transaction receipt"""

    LP = 0
    LONG = 1
    SHORT = 2
    WITHDRAWAL_SHARE = 3

def convert_prefix_to_trade_type(prefix: int) -> str:
    return HyperdrivePrefix(prefix).name

def decode_asset_id(asset_id: int) -> tuple[int, int]:
    r"""Decodes a transaction asset ID into its constituent parts of an identifier, data, and a timestamp.

    First calculate the prefix mask by left-shifting 1 by 248 bits and subtracting 1 from the result.
    This gives us a bit-mask with 248 bits set to 1 and the rest set to 0.
    Then apply this mask to the input ID using the bitwise-and operator `&` to extract
    the lower 248 bits as the timestamp.
    
    The prefix is a unique asset ID which denotes the following trade types:
        LP = 0
        LONG = 1
        SHORT = 2
        WITHDRAWAL_SHARE = 3

    Arguments
    ---------
    asset_id: int
        Encoded ID from a transaction. It is a concatenation, [identifier: 8 bits][timestamp: 248 bits]

    Returns
    -------
    tuple[int, int]
        identifier, timestamp
    """
    prefix_mask = (1 << 248) - 1
    prefix = asset_id >> 248  # shr 248 bits
    timestamp = asset_id & prefix_mask  # apply the prefix mask
    return prefix, timestamp

def get_pool_details(pool_contract, debug: bool = False):
    name = pool_contract.functions.name().call()
    config_values = pool_contract.functions.getPoolConfig().call()
    config_outputs = pool_contract.functions.getPoolConfig().abi['outputs'][0]['components']
    config_keys = [i['name'] for i in config_outputs if 'name' in i]
    config = dict(zip(config_keys, config_values))
    if debug:
        print(f"POOL {pool_contract.address[:8]} ({name}) CONFIG:")
        for k,i in config.items():
            print(f" {k:<31} = {i}")
    info_values = pool_contract.functions.getPoolInfo().call(block_identifier=20684260)
    info_outputs = pool_contract.functions.getPoolInfo().abi['outputs'][0]['components']
    info_keys = [i['name'] for i in info_outputs if 'name' in i]
    info = dict(zip(info_keys, info_values))
    if debug:
        print(f"POOL {pool_contract.address[:8]} ({name}) INFO:")
        for k,i in info.items():
            print(f" {k:<31} = {i}")
        # don't subtract minimum share reserves here, because we want to reward
    # all deposited LPs, even if it can't be withdrawn (the minimum share reserves)
    adjusted_share_reserves = info['shareReserves'] - 1 * config['minimumShareReserves']
    lp_total_supply_in_vault_shares = info['lpTotalSupply'] * info['lpSharePrice'] / info['vaultSharePrice']
    # expected_vault_shares_balance = lp_total_supply_in_vault_shares + (info['longExposure'] + info['shortsOutstanding'])
    expected_vault_shares_balance = info['shareReserves'] + (info['shortsOutstanding'])
    lp_ratio = adjusted_share_reserves / lp_total_supply_in_vault_shares
    lp_diff = adjusted_share_reserves - lp_total_supply_in_vault_shares
    lp_diff_pct = lp_diff / lp_total_supply_in_vault_shares
    # TODO: update this link after merging
    # from https://github.com/delvtech/hyperdrive-experiments/pull/15/files#diff-fa01a54eac92f5f50c0df979cc947a9b502e28fa76f1add7a12aec80cd8a3a74
    lp_short_positions = info['longExposure']

    # query pool holdings of the base token
    base_token_balance = None
    if config["baseToken"] == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        # the base token is ETH
        base_token_balance = w3.eth.get_balance(pool_contract.address)
    else:
        base_token_contract = w3.eth.contract(address=config["baseToken"], abi=ERC20_ABI)
        base_token_balance = base_token_contract.functions.balanceOf(pool_contract.address).call()
    vault_shares_balance = vault_contract_address = vault_contract = None
    if "Morpho" in name:
        vault_contract_address = pool_contract.functions.vault().call()
        print(f"{vault_contract_address=}")
        vault_contract = w3.eth.contract(address=vault_contract_address, abi=MORPHO_ABI)
        morpho_market_id = w3.keccak(eth_abi.encode(  # type: ignore
            ("address", "address", "address", "address", "uint256"),
            (
                config["baseToken"],
                pool_contract.functions.collateralToken().call(),
                pool_contract.functions.oracle().call(),
                pool_contract.functions.irm().call(),
                pool_contract.functions.lltv().call(),
            ),
        ))
        vault_shares_balance = vault_contract.functions.position(morpho_market_id,pool_contract.address).call()[0]
    elif config["vaultSharesToken"] != "0x0000000000000000000000000000000000000000":
        vault_shares_contract = w3.eth.contract(address=config["vaultSharesToken"], abi=ERC20_ABI)
        vault_shares_balance = vault_shares_contract.functions.balanceOf(pool_contract.address).call()
    short_rewardable_tvl = info['shortsOutstanding']
    lp_rewardable_tvl = vault_shares_balance - short_rewardable_tvl
    if debug:
        print("  === calculated values ===")
        print(f" {'lp_ratio':<31} = {lp_ratio}")
        print(f" {'adjusted_share_reserves':<31} = {adjusted_share_reserves}")
        print(f" {'lp_total_supply_in_vault_shares':<31} = {lp_total_supply_in_vault_shares}")
        print(f" {'lp_diff':<31} = {lp_diff}")
        print(f" {'lp_diff_pct':<31} = {lp_diff_pct}")
        print(f" {'base_token_balance':<31} = {base_token_balance}")
        # print(f" {'expected_vault_shares_balance':<31} = {expected_vault_shares_balance/1e18}")
        if "Morpho" in name:
            print(f" {'vault_contract':<31} = {vault_contract_address}")
        print(f" {'vault_shares_balance':<31} = {vault_shares_balance}")
        # if vault_shares_balance:
        #     vault_shares_balance_minus_shorts = vault_shares_balance - info['shortsOutstanding']
        #     print(f" {'vault_shares_balance_minus_shorts':<31} = {vault_shares_balance_minus_shorts/1e18 if vault_shares_balance_minus_shorts else vault_shares_balance_minus_shorts}")
        print(f" {'lp_short_positions':<31} = {lp_short_positions}")
        print(f" {'lp_rewardable_tvl':<31} = {lp_rewardable_tvl}")
        print(f" {'short_rewardable_tvl':<31} = {short_rewardable_tvl}")

    return config, info, adjusted_share_reserves, lp_ratio, name, vault_shares_balance, lp_rewardable_tvl, short_rewardable_tvl

def get_pool_positions(pool_contract, pool_users, pool_ids, lp_ratio, lp_rewardable_tvl, short_rewardable_tvl, debug: bool = False):
    # sourcery skip: extract-method
    pool_positions = []
    rewardable_by_prefix = {
        0: Decimal(lp_rewardable_tvl),  # LPs get a share of the LP rewardable TVL
        1: Decimal(0),  # longs get nothing since they have no exposure to the variable rate
        2: Decimal(short_rewardable_tvl),  # shorts get a share of the Short rewardable TVL
        3: Decimal(lp_rewardable_tvl),  # withdrawal shares get rewarded the same as LPs
    }
    bal_by_prefix = {0: Decimal(0), 1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    shares_by_prefix = {0: Decimal(0), 1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    for user,id in itertools.product(pool_users, pool_ids):
        trade_type, prefix, timestamp = get_trade_details(int(id))
        bal = pool_contract.functions.balanceOf(int(id),user).call()
        rewardable_tvl = Decimal(calc_rewardable_tvl(lp_ratio, trade_type, bal))
        if bal > Decimal(1):
            if debug:
                print(f"user={user[:8]} {trade_type}({prefix=}) {timestamp=} balance={bal} rewardable={rewardable_tvl}")
            pool_positions.append([user, trade_type, prefix, timestamp, bal, rewardable_tvl, Decimal(0)])
            bal_by_prefix[prefix] += bal
    for position in pool_positions:
        prefix = position[2]
        if bal_by_prefix[prefix] != Decimal(0):
            share_of_rewardable = position[4] / bal_by_prefix[prefix]
            position[6] = (rewardable_by_prefix[prefix] * share_of_rewardable).quantize(Decimal('0'))

    # Calculate shares by prefix
    shares_by_prefix = {prefix: sum(position[6] for position in pool_positions if position[2] == prefix) for prefix in range(4)}

    # Correction step
    combined_prefixes = [(0, 3), (2,)]  # Treat prefixes 0 and 3 together, 2 separately
    for prefixes in combined_prefixes:
        combined_shares = sum(shares_by_prefix[p] for p in prefixes)
        combined_rewardable = rewardable_by_prefix[prefixes[0]]  # take rewardable_by_prefix of first prefix
        print(f"{prefixes=}")
        print(f"{combined_shares=}")
        print(f"{combined_rewardable=}")
        if combined_shares != combined_rewardable:
            diff = combined_rewardable - combined_shares
            # Find the position with the largest share among the combined prefixes
            max_position = max((p for p in pool_positions if p[2] in prefixes), key=lambda x: x[6])
            print(f"found {diff=} in {prefixes=}, adjusting\n{max_position=}")
            max_position[6] += diff
            print(f"{max_position=}")

    # Re-calculate shares by prefix
    shares_by_prefix = {prefix: sum(position[6] for position in pool_positions if position[2] == prefix) for prefix in range(4)}

    # combine LPs and withdrawal shares into subtotals to check accuracy
    subtotals_by_prefix = {0: shares_by_prefix[0] + shares_by_prefix[3], 1: shares_by_prefix[1], 2: shares_by_prefix[2]}
    # each subtotal (shares_by_prefix) should match the total (rewardable_by_prefix)
    for prefix in subtotals_by_prefix:
        print(f"{prefix=:<3} balance={bal_by_prefix[prefix]:>24} shares={subtotals_by_prefix[prefix]:>24} rewardable={rewardable_by_prefix[prefix]:>24}")
        if subtotals_by_prefix[prefix] == rewardable_by_prefix[prefix]:
            print(f" check subtotals_by_prefix == rewardable_by_prefix ({subtotals_by_prefix[prefix]} == {rewardable_by_prefix[prefix]}) ✅")
        else:
            print(f" check subtotals_by_prefix == rewardable_by_prefix ({subtotals_by_prefix[prefix]} != {rewardable_by_prefix[prefix]}) ❌")
    return pool_positions

def get_trade_details(asset_id: int) -> tuple[str, int, int]:
    prefix, timestamp = decode_asset_id(asset_id)
    trade_type = convert_prefix_to_trade_type(prefix)
    return trade_type, prefix, timestamp

def calc_rewardable_tvl(lp_ratio: float, trade_type: str, bal: int):
    # sourcery skip: remove-unnecessary-cast, raise-specific-error
    rewardable_tvl = None
    match trade_type:
        case "LP":
            rewardable_tvl = bal * lp_ratio
        case "LONG":
            rewardable_tvl = 0
        case "SHORT":
            rewardable_tvl = bal
        case "WITHDRAWAL_SHARE":
            rewardable_tvl = bal * lp_ratio
        case _:
            raise Exception(f"unknown trade type {trade_type}")
    return int(rewardable_tvl)
