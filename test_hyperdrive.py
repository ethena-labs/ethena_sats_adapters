# %%
import time
from decimal import Decimal

import pandas as pd

from constants.hyperdrive import (
    HYPERDRIVE_MORPHO_ABI,
    HYPERDRIVE_REGISTRY,
    HYPERDRIVE_REGISTRY_ABI,
)
from utils.hyperdrive import (
    get_hyperdrive_participants,
    get_pool_details,
    get_pool_positions,
)
from utils.web3_utils import w3

## Import
HYPERDRIVE_REGISTRY = w3.eth.contract(address=w3.to_checksum_address(HYPERDRIVE_REGISTRY), abi=HYPERDRIVE_REGISTRY_ABI)
number_of_instances = HYPERDRIVE_REGISTRY.functions.getNumberOfInstances().call()
instance_list = HYPERDRIVE_REGISTRY.functions.getInstancesInRange(0,number_of_instances).call()

pool_to_test = instance_list[10]  # 5 = ezETH, 3 = sUSDe/DAI
print(f"=== pool to test: {pool_to_test} ===")
start_time = time.time()
pool_users, pool_ids = get_hyperdrive_participants(pool_to_test, cache=True)
pool_to_test_contract = w3.eth.contract(address=w3.to_checksum_address(pool_to_test), abi=HYPERDRIVE_MORPHO_ABI)
config, info, adjusted_share_reserves, lp_ratio, name, vault_shares_balance, lp_rewardable_tvl, short_rewardable_tvl = get_pool_details(pool_to_test_contract, debug=True)
print(f"=== {name} ===")
pool_positions = get_pool_positions(
    pool_contract=pool_to_test_contract,
    pool_users=pool_users,
    pool_ids=pool_ids,
    lp_ratio=lp_ratio,
    lp_rewardable_tvl=lp_rewardable_tvl,
    short_rewardable_tvl=short_rewardable_tvl,
    debug=True,
)

# display stuff
pool_positions_df = pd.DataFrame(pool_positions, columns=["user","type","prefix","timestamp","balance","ratio_amount","share_amount"])
pool_positions_df = pool_positions_df.astype({'prefix': str, 'timestamp': str})
pool_positions_df.loc['Total', 'balance'] = pool_positions_df['balance'].sum()
pool_positions_df.loc['Total', 'ratio_amount'] = pool_positions_df['ratio_amount'].sum()
pool_positions_df.loc['Total', 'share_amount'] = pool_positions_df['share_amount'].sum()
total_by_share_amount = Decimal(pool_positions_df.loc['Total','share_amount'])
if vault_shares_balance == total_by_share_amount:
    print(f"vault_shares_balance == total_by_share_amount ({vault_shares_balance} == {total_by_share_amount}) ✅")
else:
    print(f"vault_shares_balance != total_by_share_amount ({vault_shares_balance} != {total_by_share_amount}) ❌")
pool_positions_df['Diff'] = pool_positions_df['share_amount'] - pool_positions_df['ratio_amount']
pool_positions_df['DiffPct'] = 0.0
pool_positions_df['DiffPct'] = pool_positions_df.apply(
    lambda row: row['DiffPct'] if row['ratio_amount'] == 0 else row['Diff'] / row['ratio_amount'],
    axis=1,
)
print(pool_positions_df)
