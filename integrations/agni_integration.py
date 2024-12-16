from typing import Dict, List, Optional, Set

from eth_typing import ChecksumAddress

from constants.agni import (
    usde_cmeth_025,
    usde_usdt_001,
    susde_usde_005,
    usdc_usde_001,
)
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from utils.agni import (
    get_agni_pool_info_list,
    get_agni_all_user_balance
)


class AgniIntegration(
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
            Chain.MANTLE,
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
        pool_info_list = get_agni_pool_info_list(
            {usde_cmeth_025, usde_usdt_001, susde_usde_005, usdc_usde_001},
            start_block,
            end_block
        )

        block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        for block in blocks:
            user_data = {}
            for pool_info in pool_info_list:
                pool_user_balance = get_agni_all_user_balance(pool_info, pool_info_list[pool_info], block)
                for user in pool_user_balance:
                    if user not in user_data:
                        user_data[user] = 0
                    user_data[user] = pool_user_balance[user] + user_data[user]
            block_data[block] = user_data
        return block_data


if __name__ == "__main__":
    example_integration = AgniIntegration(IntegrationID.AGNI, 72671947)
    print(
        example_integration.get_block_balances(
            cached_data={}, blocks=[72671949]
        )
    )
    # Example output:
    # {72671949: {'0x71Fb53Afc7E36C3f11BC1bdBBAB7B6FC3E552eb6': 1523973.12}}
