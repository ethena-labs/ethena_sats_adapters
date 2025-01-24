from typing import Dict, List, Optional, Set

from eth_typing import ChecksumAddress

from constants.infinityPools import (
    START_BLOCK,
    usdc_sUSDe,
    wstETH_sUSDe
)
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from utils.infinityPools import (
    get_infinityPools_info_list,
    get_infinityPool_all_user_balance
)


class InfinityPoolsIntegration(
    Integration
):  # TODO: Change ProtocolNameIntegration to the name of the protocol
    def __init__(
            self,
            integration_id: IntegrationID,
            start_block: int,
            reward_multiplier: int = 1,
            balance_multiplier: int = 1,
            excluded_addresses: Optional[Set[ChecksumAddress]] = None
    ):
        super().__init__(
            integration_id,
            start_block,
            Chain.BASE,
            None,
            reward_multiplier,
            balance_multiplier,
            excluded_addresses,
        )

    def get_block_balances(
            self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:

        start_block = self.start_block
        # last_block_cache_data = {}
        # if len(cached_data) > 0:
        #     start_block = max(cached_data.keys())
        #     last_block_cache_data = cached_data[start_block]

        end_block = max(blocks)
        pool_info_list = get_infinityPools_info_list(
            {usdc_sUSDe, wstETH_sUSDe},
            start_block,
            end_block
        )
        # print("pool_info_list", pool_info_list)

        block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        for block in blocks:
            user_data: Dict[ChecksumAddress, float] = {}
            for pool_info in pool_info_list:
                pool_user_balance = get_infinityPool_all_user_balance(
                    pool_info_list[pool_info], block)
                # print(pool_user_balance)
                for user in pool_user_balance:
                    if user not in user_data:
                        user_data[user] = 0
                    user_data[user] = pool_user_balance[user] + user_data[user]
            block_data[block] = user_data
        return block_data


if __name__ == "__main__":
    example_integration = InfinityPoolsIntegration(
        IntegrationID.INFINITYPOOLS, START_BLOCK)
    print(
        example_integration.get_block_balances(
            cached_data={}, blocks=[25037239]
        )
    )
    # Example output:
    # {24813472: {'0x71Fb53Afc7E36C3f11BC1bdBBAB7B6FC3E552eb6': 1523973.12}}
