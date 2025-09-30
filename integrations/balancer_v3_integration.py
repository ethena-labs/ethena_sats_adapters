from typing import List, Optional, Set
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from utils.balancer import (
    get_vault_v3_pool_token_balance,
    get_potential_token_holders,
    get_user_balance,
    get_token_supply,
)
from constants.balancer_v3 import INTEGRATION_CONFIGS


class BalancerV3Integration(Integration):
    def __init__(self, integration_id: IntegrationID):
        config = INTEGRATION_CONFIGS.get(integration_id)
        if not config:
            raise ValueError(
                f"No configuration found for integration ID: {integration_id}"
            )

        super().__init__(
            integration_id,
            config.start_block,
            config.chain,
            [],
            20,
            1,
            None,
            None,
        )

        self.pool_address = config.pool_address
        self.gauge_address = config.gauge_address
        self.aura_address = config.aura_address
        self.incentivized_token = config.incentivized_token
        self.incentivized_token_decimals = config.incentivized_token_decimals

    def get_balance(self, user: str, block: int | str = "latest") -> float:
        """
        Retrieve the balance of the user in the incentivized Ethena token.

        This method calculates the user's token balance based on the share of Balancer Pool Tokens (BPTs)
        staked either directly in Balancer gauges or via Aura Finance.
        """
        gauge_balance = (
            0
            if self.gauge_address is None
            else get_user_balance(self.chain, user, self.gauge_address, block)
        )
        aura_balance = (
            0
            if self.aura_address is None
            else get_user_balance(self.chain, user, self.aura_address, block)
        )

        bpt_supply = get_token_supply(self.chain, self.pool_address, block)

        user_balance = gauge_balance + aura_balance

        incentivized_token_balance = get_vault_v3_pool_token_balance(
            self.chain, self.pool_address, self.incentivized_token, block
        )

        user_share = user_balance / bpt_supply

        return (
            user_share
            * incentivized_token_balance
            / pow(10, self.incentivized_token_decimals)
        )

    def get_participants(
        self,
        blocks: Optional[List[int]],
    ) -> Set[str]:
        """
        Retrieve the set of all unique participants who might have Balancer Pool Tokens (BPTs).
        """
        bpt_holders = get_potential_token_holders(
            self.chain, self.pool_address, self.start_block
        )

        gauge_holders = (
            []
            if self.gauge_address is None
            else get_potential_token_holders(
                self.chain, self.gauge_address, self.start_block
            )
        )

        aura_holders = (
            []
            if self.aura_address is None
            else get_potential_token_holders(
                self.chain, self.aura_address, self.start_block
            )
        )

        return set(bpt_holders + aura_holders + gauge_holders)


if __name__ == "__main__":
    balancer = BalancerV3Integration(IntegrationID.BALANCER_V3_PLASMA_USDE_USDT)
    participants = balancer.get_participants(None)
    balances = balancer.get_balance(list(participants)[0])
