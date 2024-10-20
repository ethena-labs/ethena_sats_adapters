import itertools
from decimal import Decimal, getcontext

from dotenv import load_dotenv

from constants.hyperdrive import ERC20_ABI,HYPERDRIVE_MORPHO_ABI,HyperdrivePrefix
from utils.web3_utils import fetch_events_logs_with_retry,w3

load_dotenv()

PAGE_SIZE = 1900
getcontext().prec = 100  # Set precision for Decimal calculations

def get_first_contract_block(contract_address):
    # do binary search up to latest block
    latest_block = w3.eth.get_block_number()
    earliest_block = 0
    while earliest_block < latest_block:
        mid_block = (earliest_block + latest_block) // 2
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

def get_hyperdrive_participants(pool):
    target_block = w3.eth.get_block_number()
    all_users = set()
    all_ids = set()
    start_block = get_first_contract_block(pool)
    assert all_users is not None, "error: all_users is None"
    assert all_ids is not None, "error: all_ids is None"
    assert start_block is not None, "error: start_block is None"
    contract = w3.eth.contract(address=pool, abi=HYPERDRIVE_MORPHO_ABI)
    
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
        current_block = to_block

    return all_users, all_ids

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

def get_pool_details(pool_contract):
    name = pool_contract.functions.name().call()
    config_values = pool_contract.functions.getPoolConfig().call()
    config_outputs = pool_contract.functions.getPoolConfig().abi['outputs'][0]['components']
    config_keys = [i['name'] for i in config_outputs if 'name' in i]
    config = dict(zip(config_keys, config_values))
    info_values = pool_contract.functions.getPoolInfo().call()
    info_outputs = pool_contract.functions.getPoolInfo().abi['outputs'][0]['components']
    info_keys = [i['name'] for i in info_outputs if 'name' in i]
    info = dict(zip(info_keys, info_values))

    # query pool holdings
    vault_shares_balance = None
    if config["vaultSharesToken"] != "0x0000000000000000000000000000000000000000":
        vault_shares_contract = w3.eth.contract(address=config["vaultSharesToken"], abi=ERC20_ABI)
        vault_shares_balance = vault_shares_contract.functions.balanceOf(pool_contract.address).call()
    short_rewardable_tvl = info['shortsOutstanding']
    lp_rewardable_tvl = vault_shares_balance - short_rewardable_tvl

    return config, info, name, vault_shares_balance, lp_rewardable_tvl, short_rewardable_tvl

def get_pool_positions(pool_contract, pool_users, pool_ids, lp_rewardable_tvl, short_rewardable_tvl, block = None, debug: bool = False):
    pool_positions = []
    combined_prefixes = [(0, 3), (2,)]  # Treat prefixes 0 and 3 together, 2 separately
    bal_by_prefix = {0: Decimal(0), 1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}

    # First pass: collect balances
    for user, id in itertools.product(pool_users, pool_ids):
        trade_type, prefix, timestamp = get_trade_details(int(id))
        bal = pool_contract.functions.balanceOf(int(id), user).call(block_identifier=block or "latest")
        if bal > Decimal(1):
            if debug:
                print(f"user={user[:8]} {trade_type:<4}({prefix=}) {timestamp=:>12} balance={bal:>32}")
            pool_positions.append([user, trade_type, prefix, timestamp, bal, Decimal(0)])
            bal_by_prefix[prefix] += bal
    # manually hard-code a withdrawal share position
    # bal = 24101344855221864785272839529
    # pool_positions.append(["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "WITHDRAWAL_SHARE", 3, 1678908800, bal, Decimal(0)])
    # bal_by_prefix[3] += bal

    # Second pass: calculate shares (prefix 1 (longs) get nothing, so we skip it)
    for position in pool_positions:
        prefix = position[2]
        if prefix in [0, 3]:  # assign rewards for LPs and withdrawal shares
            combined_lp_balance = bal_by_prefix[0] + bal_by_prefix[3]  # combine LP and withdrawal share balance
            if combined_lp_balance != Decimal(0):
                share_of_rewardable = position[4] / combined_lp_balance
                position[5] = (lp_rewardable_tvl * share_of_rewardable).quantize(Decimal('0'))
        elif prefix == 2:  # assign rewards for shorts
            if bal_by_prefix[2] != Decimal(0):
                share_of_rewardable = position[4] / bal_by_prefix[2]
                position[5] = (short_rewardable_tvl * share_of_rewardable).quantize(Decimal('0'))

    # Correction step to fix rounding errors
    for prefixes in combined_prefixes:
        combined_shares = sum(position[5] for position in pool_positions if position[2] in prefixes)
        combined_rewardable = lp_rewardable_tvl if prefixes[0] == 0 else short_rewardable_tvl
        if debug:
            print(f"{prefixes=}")
            print(f"{combined_shares=}")
            print(f"{combined_rewardable=}")
        if combined_shares != combined_rewardable:
            diff = combined_rewardable - combined_shares
            # Find the position with the largest share among the combined prefixes
            max_position = max((p for p in pool_positions if p[2] in prefixes), key=lambda x: x[5])
            if debug:
                print(f"found {diff=} in {prefixes=}, adjusting\n{max_position=}")
            max_position[5] += diff
            if debug:
                print(f"{max_position=}")

    # Make sure rewards add up to rewardable TVL
    for prefixes in combined_prefixes:
        combined_shares = sum(position[5] for position in pool_positions if position[2] in prefixes)
        combined_rewardable = lp_rewardable_tvl if prefixes[0] == 0 else short_rewardable_tvl
        if combined_shares == combined_rewardable:
            print(f"for prefixes={prefixes}, check combined_shares == combined_rewardable ({combined_shares} == {combined_rewardable}) ✅")
        else:
            print(f"for prefixes={prefixes}, check combined_shares == combined_rewardable ({combined_shares} != {combined_rewardable}) ❌")

    return pool_positions

def get_trade_details(asset_id: int) -> tuple[str, int, int]:
    prefix, timestamp = decode_asset_id(asset_id)
    trade_type = HyperdrivePrefix(prefix).name
    return trade_type, prefix, timestamp
