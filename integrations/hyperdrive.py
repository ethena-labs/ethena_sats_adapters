from decimal import Decimal
from constants.chains import Chain
from models.integration import Integration
from constants.integration_ids import IntegrationID
from constants.hyperdrive import HYPERDRIVE_SUSDE_POOL_ADDRESS, HYPERDRIVE_SUSDE_POOL_DEPLOYMENT_BLOCK, HYPERDRIVE_MORPHO_ABI
from utils.hyperdrive import get_hyperdrive_participants, get_pool_details, get_pool_positions
from utils.web3_utils import w3

class Hyperdrive(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.HYPERDRIVE_SUSDE,
            HYPERDRIVE_SUSDE_POOL_DEPLOYMENT_BLOCK,
            Chain.ETHEREUM,
            None,
            20,
            1,
            None,
            None,
        )
        self.pool_ids = None
        self.pool_users = None
        self.pool_positions = None

    def update_participants(self):
        self.pool_users, self.pool_ids = get_hyperdrive_participants(
            pool=HYPERDRIVE_SUSDE_POOL_ADDRESS,
            start_block=HYPERDRIVE_SUSDE_POOL_DEPLOYMENT_BLOCK,
        )

    def get_participants(self):
        self.update_participants()
        return self.pool_users

    def get_balance(self, user: str, block: int) -> float:
        # update hyperdrive participants
        if self.pool_positions is None:
            if self.pool_users is None:
                self.update_participants()
            # get pool positions
            pool_contract = w3.eth.contract(address=w3.to_checksum_address(HYPERDRIVE_SUSDE_POOL_ADDRESS), abi=HYPERDRIVE_MORPHO_ABI)
            _, lp_rewardable_tvl, short_rewardable_tvl = get_pool_details(pool_contract)
            self.pool_positions = get_pool_positions(
                pool_contract=pool_contract,
                pool_users=self.pool_users,
                pool_ids=self.pool_ids,
                lp_rewardable_tvl=lp_rewardable_tvl,
                short_rewardable_tvl=short_rewardable_tvl,
                block=block,
            )
        # get the user's balance
        rewardable_tvl = sum(position[5] for position in self.pool_positions if position[0] == user)
        return rewardable_tvl / 1e18

    def test_hyperdrive(self):
        self.update_participants()
        pool_contract = w3.eth.contract(address=w3.to_checksum_address(HYPERDRIVE_SUSDE_POOL_ADDRESS), abi=HYPERDRIVE_MORPHO_ABI)
        vault_shares_balance, lp_rewardable_tvl, short_rewardable_tvl = get_pool_details(pool_contract)
        pool_positions = get_pool_positions(
            pool_contract=pool_contract,
            pool_users=self.pool_users,
            pool_ids=self.pool_ids,
            lp_rewardable_tvl=lp_rewardable_tvl,
            short_rewardable_tvl=short_rewardable_tvl,
        )

        # Make sure rewards add up to rewardable TVL
        combined_prefixes = [(0, 3), (2,)]  # Treat prefixes 0 and 3 together, 2 separately
        for prefixes in combined_prefixes:
            combined_shares = sum(position[5] for position in pool_positions if position[2] in prefixes)
            combined_rewardable = lp_rewardable_tvl if prefixes[0] == 0 else short_rewardable_tvl
            if combined_shares == combined_rewardable:
                print(f"for prefixes={prefixes}, check combined_shares == combined_rewardable ({combined_shares} == {combined_rewardable}) ✅")
            else:
                print(f"for prefixes={prefixes}, check combined_shares == combined_rewardable ({combined_shares} != {combined_rewardable}) ❌")

        total_rewardable = Decimal(sum(position[5] for position in pool_positions))
        if vault_shares_balance == total_rewardable:
            print(f"vault_shares_balance == total_rewardable ({vault_shares_balance} == {total_rewardable}) ✅")
        else:
            print(f"vault_shares_balance != total_rewardable ({vault_shares_balance} != {total_rewardable}) ❌")

if __name__ == "__main__":
    hyperdrive = Hyperdrive()
    hyperdrive.test_hyperdrive()
