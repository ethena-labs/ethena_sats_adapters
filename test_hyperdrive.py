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

pool_to_test = instance_list[5]  # 5 = ezETH, 3 = sUSDe/DAI
print(f"=== pool to test: {pool_to_test} ===")
start_time = time.time()
pool_users, pool_ids = get_hyperdrive_participants(pool_to_test, cache=True)
pool_to_test_contract = w3.eth.contract(address=w3.to_checksum_address(pool_to_test), abi=HYPERDRIVE_MORPHO_ABI)
config, info, name, vault_shares_balance, lp_rewardable_tvl, short_rewardable_tvl = get_pool_details(pool_to_test_contract, debug=True)
print(f"=== {name} ===")
pool_positions = get_pool_positions(
    pool_contract=pool_to_test_contract,
    pool_users=pool_users,
    pool_ids=pool_ids,
    lp_rewardable_tvl=lp_rewardable_tvl,
    short_rewardable_tvl=short_rewardable_tvl,
    debug=True,
)

# display stuff
pool_positions_df = pd.DataFrame(pool_positions, columns=["user","type","prefix","timestamp","balance","rewardable"])  # type: ignore
pool_positions_df = pool_positions_df.astype({'prefix': str, 'timestamp': str})
pool_positions_df.loc['Total', 'balance'] = pool_positions_df['balance'].sum()
pool_positions_df.loc['Total', 'rewardable'] = pool_positions_df['rewardable'].sum()
total_rewardable = Decimal(pool_positions_df.loc['Total','rewardable'])
if vault_shares_balance == total_rewardable:
    print(f"vault_shares_balance == total_rewardable ({vault_shares_balance} == {total_rewardable}) ✅")
else:
    print(f"vault_shares_balance != total_rewardable ({vault_shares_balance} != {total_rewardable}) ❌")
print(pool_positions_df)
