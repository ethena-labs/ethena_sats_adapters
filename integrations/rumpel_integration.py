from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress

import math
from utils.web3_utils import w3, fetch_events_logs_with_retry, fetch_transaction_receipt_with_retry, call_with_retry
from constants.rumpel import KPSATS_POOLS, UNIV3_NONFUNGIBLE_POSITION_MANAGER_CONTRACT, SENA_ADDRESS,UNIV3_POOL_ABI

def calculate_lp_tokens(tick, tick_lower, tick_upper, sqrt_price, liquidity):
    if liquidity == 0:
        return [0, 0]
    # if abs(tick_lower) > MAX_TICK_RANGE or abs(tick_upper) > MAX_TICK_RANGE:
    #     return [0, 0]
    t0 = 0
    t1 = 0
    sqrt_ratio_u = math.sqrt(1.0001**tick_upper)
    sqrt_ratio_l = math.sqrt(1.0001**tick_lower)
    if tick_lower < tick < tick_upper:
        t0 = liquidity * (sqrt_ratio_u - sqrt_price) / (sqrt_price * sqrt_ratio_u)
        t1 = liquidity * (sqrt_price - sqrt_ratio_l)
    elif tick >= tick_upper:
        t1 = liquidity * (sqrt_ratio_u - sqrt_ratio_l)
    else:
        t0 = liquidity * (sqrt_ratio_u - sqrt_ratio_l) / (sqrt_ratio_u * sqrt_ratio_l)
    return [abs(t0 / 10**18), abs(t1 / 10**18)]

class RumpelIntegration(
    CachedBalancesIntegration
):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block: Optional[int] = None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func: Optional[Callable[[int, str], int]] = None,
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            summary_cols,
            reward_multiplier,
            balance_multiplier,
            excluded_addresses,
            end_block,
            ethereal_multiplier,
            ethereal_multiplier_func,
        )

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        users: Dict[int, Dict[ChecksumAddress, float]] = {}

        for block in blocks:
            for kpsat_pool in KPSATS_POOLS:
                if(block < kpsat_pool.deployed_block):
                    continue
                

                start = kpsat_pool.deployed_block
                end = block
                users[end] = {}

                pool = w3.eth.contract(
                    address=kpsat_pool.pool_address,
                    abi=UNIV3_POOL_ABI,
                )
                nfpm = UNIV3_NONFUNGIBLE_POSITION_MANAGER_CONTRACT

                poolState = call_with_retry(pool.functions.slot0(), block=end)
                pool_price_sqrt_x96 = poolState[0]
                pool_tick = poolState[1]

                # query all mint events directly from the pool
                mints = fetch_events_logs_with_retry(
                            "Rumpel liquidity Minted",
                            pool.events.Mint(),
                            start,
                            end,
                        )
                
                lp_positions = set()
                increase_liquidity_event = UNIV3_NONFUNGIBLE_POSITION_MANAGER_CONTRACT.events.IncreaseLiquidity()
                increase_liquidity_param_types = [param['type'] for param in increase_liquidity_event.abi['inputs']]
                increase_liquidity_signature = f"{increase_liquidity_event.event_name}({','.join(increase_liquidity_param_types)})"
                topic_hash = w3.keccak(text=increase_liquidity_signature).hex()

                # get the IncreaseLiquidity event from the NonFungiblePositionManager Increase Liquidity Event
                # dev: if the tx updates multiple pools, this will include out of scope positions.
                # for this reason there is a check on the positions tokens
                for mint in mints:
                    tx = fetch_transaction_receipt_with_retry(Chain.ETHEREUM, mint["transactionHash"].hex());
                    for log in tx.logs:
                        if(log.topics[0].hex() == topic_hash):
                            token_id = int.from_bytes(log.topics[1], 'big')
                            lp_positions.add(token_id);


                # get each positions owner and data, calculate the users balance, and update storage
                for lp_position in lp_positions:
                    owner = call_with_retry(nfpm.functions.ownerOf(lp_position), block=end)
                    position_data = call_with_retry(nfpm.functions.positions(lp_position), block=end)

                    # check the position is for this pool
                    token0 = position_data[2]
                    token1 = position_data[3]
                    if(token0 != kpsat_pool.kpsats_address or token1 != SENA_ADDRESS):
                        continue

                    lower_tick = position_data[5]
                    upper_tick = position_data[6]
                    liquidity = position_data[7]

                    balances = calculate_lp_tokens(pool_tick, lower_tick, upper_tick, pool_price_sqrt_x96 / (2**96), liquidity)

                    if users.get(end, {}).get(owner) is not None:
                        users[end][owner] += balances[1]
                    else:
                        users[end][owner] = balances[1]

        return users
        


if __name__ == "__main__":
    example_integration = RumpelIntegration(
        integration_id=IntegrationID.RUMPEL_SENA_LP,
        start_block=KPSATS_POOLS[0].deployed_block,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=40000000,
    )
    print(
        example_integration.get_block_balances(
            cached_data={}, blocks=[21645700, 21645701, 21645702, 22375313]
        )
    )