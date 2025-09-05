import math
from typing import Dict, List, Optional, Set
from eth_typing import ChecksumAddress
from constants.thruster import (
    HYPERLOCK_DEPOSIT_ADDRESS,
    JUICE_USDE_VAULT_ADDR,
    THRUSTER_USDE_POOL_ADDRESS,
)
from constants.thruster import (
    thruster_nfp_contract,
    thruster_usde_pool_contract,
)
from constants.summary_columns import SummaryColumn
from constants.chains import Chain
from integrations.deposit_ids_integration import DepositIdsIntegration
from integrations.integration_ids import IntegrationID as IntID

from utils.thruster import (
    get_pool_price,
    get_pool_tick,
    get_thruster_users,
    get_thrusters_position_balance,
)


class ThrusterIntegration(DepositIdsIntegration):
    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        pool_address: ChecksumAddress,
    ):
        super().__init__(
            integration_id,
            start_block,
            Chain.BLAST,
            [SummaryColumn.THRUSTER_POOL_PTS],
            30,
            {HYPERLOCK_DEPOSIT_ADDRESS, JUICE_USDE_VAULT_ADDR},
        )
        self.pool_address = pool_address

    def get_nfp_contract(self):
        return thruster_nfp_contract

    def get_deposit_ids_balances(
        self, deposit_ids: Set[int], user: ChecksumAddress, block: int
    ) -> float:
        try:
            if block < self.start_block or len(deposit_ids) == 0:
                return 0
            token_ids = deposit_ids
            user_t0_balances = 0
            user_t1_balances = 0
            sqrt_price = math.sqrt(get_pool_price(thruster_usde_pool_contract, block))
            tick = get_pool_tick(thruster_usde_pool_contract, block)
            nfp_contract = self.get_nfp_contract()
            for token_id in token_ids:
                # This is the best approach to check if the token ID exists (handling the exception and continue),
                # since performing any call on the smart contract to check if the token ID exists at the current block
                # will revert anyways and its one RPC call more for each token ID
                try:
                    owner = nfp_contract.functions.ownerOf(token_id).call(
                        block_identifier=block
                    )
                    if owner != user:
                        continue
                    [t0, t1] = get_thrusters_position_balance(
                        token_id, block, tick, sqrt_price
                    )
                    user_t0_balances += t0
                    user_t1_balances += t1
                except Exception:
                    continue
            return round(user_t0_balances + user_t1_balances, 4)
        except Exception as e:
            err_msg = (
                f"[{self.integration_id.value}] Issue getting balance for {user} at \
                      block {block}. Returning 0. "
                f"Exception: {e}"
            )
            print(err_msg)
            return 0

    def get_participants_with_deposit_ids(
        self, blocks: List[int], cache: Optional[Dict[ChecksumAddress, Set[int]]] = None
    ) -> Dict[ChecksumAddress, Set[int]]:
        cached_data: Dict[ChecksumAddress, Set[int]] = cache or {}
        end_block = max(blocks) if len(blocks) else self.end_block
        users_and_token_ids = get_thruster_users(
            self.pool_address, self.start_block, end_block
        )
        for user, token_ids in users_and_token_ids.items():
            if user not in cached_data:
                cached_data[user] = set()
            cached_data[user].update(token_ids)
        return cached_data


if __name__ == "__main__":
    print("=" * 60)
    print("THRUSTER INTEGRATION ANALYSIS")
    print("=" * 60)

    thruster_integration = ThrusterIntegration(
        IntID.THRUSTER_USDE_POOL, 4025647, THRUSTER_USDE_POOL_ADDRESS
    )

    BLOCK = 4400000

    print(f"Block: {BLOCK:,}")
    print(f"Pool: {THRUSTER_USDE_POOL_ADDRESS}")
    print("-" * 60)

    participants_with_deposit_ids = (
        thruster_integration.get_participants_with_deposit_ids([BLOCK])
    )

    print(f"Found {len(participants_with_deposit_ids)} participants with deposit IDs")
    print("-" * 60)

    if participants_with_deposit_ids:
        print("PARTICIPANT BALANCES:")
        print("-" * 60)

        total_balance = 0.0
        for i, participant in enumerate(participants_with_deposit_ids, 1):
            deposit_ids = participants_with_deposit_ids[participant]
            balance = thruster_integration.get_deposit_ids_balances(
                deposit_ids, participant, BLOCK
            )
            total_balance += balance

            print(f"{i:2d}. {participant}")
            print(f"    Deposit IDs: {sorted(list(deposit_ids))}")
            print(f"    Balance: {balance:,.6f}")
            print()

        print("=" * 60)
        print("SUMMARY:")
        print(f"  Total Participants: {len(participants_with_deposit_ids)}")
        print(f"  Total Balance: {total_balance:,.6f}")
        print("=" * 60)
    else:
        print("No participants found for this block")
        print("=" * 60)
