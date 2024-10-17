# %%
from decimal import Decimal

from constants.hyperdrive import HYPERDRIVE_MORPHO_ABI, HYPERDRIVE_SUSDE_POOL
from utils.hyperdrive import get_hyperdrive_participants, get_pool_details, get_pool_positions
from utils.web3_utils import w3

## Import
print(f"=== {HYPERDRIVE_SUSDE_POOL} ===")
pool_users, pool_ids = get_hyperdrive_participants(HYPERDRIVE_SUSDE_POOL)
pool_contract = w3.eth.contract(address=w3.to_checksum_address(HYPERDRIVE_SUSDE_POOL), abi=HYPERDRIVE_MORPHO_ABI)
_, _, name, vault_shares_balance, lp_rewardable_tvl, short_rewardable_tvl = get_pool_details(pool_contract)
print(f"=== {name} ===")
pool_positions = get_pool_positions(
    pool_contract=pool_contract,
    pool_users=pool_users,
    pool_ids=pool_ids,
    lp_rewardable_tvl=lp_rewardable_tvl,
    short_rewardable_tvl=short_rewardable_tvl,
    debug=True,
)

# display stuff
total_rewardable = Decimal(sum(position[5] for position in pool_positions))
if vault_shares_balance == total_rewardable:
    print(f"vault_shares_balance == total_rewardable ({vault_shares_balance} == {total_rewardable}) ✅")
else:
    print(f"vault_shares_balance != total_rewardable ({vault_shares_balance} != {total_rewardable}) ❌")

# %%
