import math
from typing import Dict, List, Optional, Set
from eth_typing import ChecksumAddress
from web3 import Web3
from constants.uniswap_v4 import (
    UNISWAP_V4_NFPM_ADDRESS,
    UNISWAP_V4_USDE_POOL,
    uniswap_v4_nfpm_contract,
    uniswap_v4_pm_contract,
    uniswap_v4_sv_contract,
)
from utils.web3_utils import (
    MULTICALL_ADDRESS_BY_CHAIN,
    call_with_retry,
    fetch_events_logs_with_retry,
    multicall_by_address,
    w3,
)
from constants.summary_columns import SummaryColumn
from constants.chains import Chain
from integrations.deposit_ids_integration import DepositIdsIntegration
from integrations.integration_ids import IntegrationID as IntID

PAGINATION_SIZE = 1000


def get_all_users(
    start=21688329,
    end=None,
) -> Dict[ChecksumAddress, Set[int]]:
    if end is None:
        end = w3.eth.get_block_number()

    users: Dict[ChecksumAddress, Set[int]] = {}
    ownerOf_calls = []
    token_ids = []

    while start < end:
        to_block = start + PAGINATION_SIZE
        deposits = fetch_events_logs_with_retry(
            "Users",
            uniswap_v4_pm_contract.events.ModifyLiquidity(),
            start,
            to_block,
        )
        deposits_list = list(deposits)
        print(start, to_block, len(deposits_list), "getting deposits for uniswap v4")

        for deposit in deposits_list:
            if (
                deposit["args"]["id"] == UNISWAP_V4_USDE_POOL
                and deposit["args"]["sender"] == UNISWAP_V4_NFPM_ADDRESS
            ):
                token_id = Web3.to_int(deposit["args"]["salt"])

                ownerOf_calls.append(
                    (
                        uniswap_v4_nfpm_contract,
                        uniswap_v4_nfpm_contract.functions.ownerOf.fn_name,
                        [token_id],
                    )
                )
                token_ids.append(token_id)

        print(start, to_block, len(token_ids), "found valid token ids")
        start += PAGINATION_SIZE

    # Execute multicall for all token ownerships
    if ownerOf_calls:
        multicall_results = multicall_by_address(
            wb3=w3,
            multical_address=MULTICALL_ADDRESS_BY_CHAIN[Chain.ETHEREUM],
            calls=ownerOf_calls,
            block_identifier=end,
            allow_failure=True,
        )

        # Process results
        for token_id, result in zip(token_ids, multicall_results):
            if result == None:
                continue

            try:
                owner = Web3.to_checksum_address(result[0])
            except Exception:
                continue

            if owner not in users:
                users[owner] = {token_id}
            else:
                users[owner].add(token_id)

    return users


def get_position_balance(token_id, block, tick, sqrt_price):
    try:
        [packedInfo] = call_with_retry(
            uniswap_v4_nfpm_contract.functions.positionInfo(token_id),
            block,
        )
        [liquidity] = call_with_retry(
            uniswap_v4_nfpm_contract.functions.getPositionLiquidity(token_id),
            block,
        )
    except Exception:
        print(f"token {token_id} not yet created at block {block}")
        return [0, 0]

    if liquidity == 0:
        return [0, 0]
    t0 = 0
    t1 = 0

    # tickUpper: bits 32-55 (from the right, 0-indexed)
    # tickLower: bits 8-31
    tick_upper = (packedInfo >> 32) & ((1 << 24) - 1)
    tick_lower = (packedInfo >> 8) & ((1 << 24) - 1)

    sqrt_ratio_l = math.sqrt(1.0001**tick_lower)
    sqrt_ratio_u = math.sqrt(1.0001**tick_upper)
    if tick_lower < tick < tick_upper:
        t0 = liquidity * (sqrt_ratio_u - sqrt_price) / (sqrt_price * sqrt_ratio_u)
        t1 = liquidity * (sqrt_price - sqrt_ratio_l)
    elif tick >= tick_upper:
        t1 = liquidity * (sqrt_ratio_u - sqrt_ratio_l)
    else:
        t0 = liquidity * (sqrt_ratio_u - sqrt_ratio_l) / (sqrt_ratio_u * sqrt_ratio_l)
    return [abs(t0 / 10**18), abs(t1 / 10**6)]


class UniswapV4Integration(DepositIdsIntegration):
    def __init__(self, integration_id: IntID, start_block: int):
        super().__init__(
            integration_id,
            start_block,
            Chain.ETHEREUM,
            [SummaryColumn.UNISWAP_V4_POOL_PTS],
            50,
            {},
        )

    def get_deposit_ids_balances(
        self, deposit_ids: Set[int], user: ChecksumAddress, block: int
    ) -> float:
        try:
            if block < self.start_block or len(deposit_ids) == 0:
                return 0
            token_ids = deposit_ids
            user_t0_balances = 0
            user_t1_balances = 0

            [sqrtPriceX96, tick] = call_with_retry(
                uniswap_v4_sv_contract.functions.getSlot0(token_id),
                block,
            )

            for token_id in token_ids:
                try:
                    owner = uniswap_v4_nfpm_contract.functions.ownerOf(token_id).call(
                        block_identifier=block
                    )
                    if owner != user:
                        continue
                    [t0, t1] = get_position_balance(token_id, block, tick, sqrtPriceX96)
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
        users_and_token_ids = get_all_users(self.start_block, end_block)
        for user, token_ids in users_and_token_ids.items():
            if user not in cached_data:
                cached_data[user] = set()
            cached_data[user].update(token_ids)
        return cached_data


if __name__ == "__main__":
    print("=" * 60)
    print("Uniswap V4 Integration Test")
    print("=" * 60)

    # The specific USDe pool was created at this block.
    v4_integration = UniswapV4Integration(IntID.UNISWAP_V4_POOL, 23067966)

    BLOCK = 23067966 + 2000
    # BLOCK = 23393544

    print(f"Block: {BLOCK:,}")
    print("-" * 60)

    participants_with_deposit_ids = v4_integration.get_participants_with_deposit_ids(
        [BLOCK]
    )

    print(f"Found {len(participants_with_deposit_ids)} participants with deposit IDs")
    print("-" * 60)

    if participants_with_deposit_ids:
        print("PARTICIPANT BALANCES:")
        print("-" * 60)

        total_balance = 0.0
        for i, participant in enumerate(participants_with_deposit_ids, 1):
            deposit_ids = participants_with_deposit_ids[participant]
            balance = v4_integration.get_deposit_ids_balances(
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
