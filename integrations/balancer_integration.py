from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.balancer import (
    get_vault_pool_token_balance,
    get_potential_token_holders,
    get_user_balance,
    get_bpt_supply,
)
from constants.balancer import INTEGRATION_CONFIGS


class BalancerIntegration(Integration):
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
            None,
            20,
            1,
            None,
            None,
        )

        self.pool_id = config.pool_id
        self.is_composable_pool = config.is_composable_pool
        self.gauge_address = config.gauge_address
        self.aura_address = config.aura_address
        self.incentivized_token = config.incentivized_token

    def get_balance(self, user: str, block: int) -> float:
        """
        Retrieve the balance of the user in the incentivized Ethena token.

        This method calculates the user's token balance based on the share of Balancer Pool Tokens (BPTs)
        staked either directly in Balancer gauges or via Aura Finance.
        """
        gauge_balance = get_user_balance(self.chain, user, self.gauge_address, block)
        aura_balance = get_user_balance(self.chain, user, self.aura_address, block)

        bpt_address = self.pool_id[:42]
        bpt_supply = get_bpt_supply(
            self.chain, bpt_address, self.is_composable_pool, block
        )

        user_balance = gauge_balance + aura_balance

        incentivized_token_balance = get_vault_pool_token_balance(
            self.chain, self.pool_id, self.incentivized_token, block
        )

        return incentivized_token_balance * user_balance / bpt_supply / 1e18

    def get_participants(self) -> list:
        """
        Retrieve the set of all unique participants who might have staked Balancer Pool Tokens (BPTs).

        This method identifies all addresses that have staked their BPT either directly
        in Balancer gauges or via Aura Finance. Non-staked BPT holders are not included.
        """
        gauge_holders = get_potential_token_holders(
            self.chain, self.gauge_address, self.start_block
        )
        aura_holders = get_potential_token_holders(
            self.chain, self.aura_address, self.start_block
        )

        self.participants = set(aura_holders + gauge_holders)
        return self.participants


if __name__ == "__main__":
    balancer = BalancerIntegration(IntegrationID.BALANCER_FRAXTAL_FRAX_USDE)
    # print(balancer.get_participants())
    print(balancer.get_balance("0x854B004700885A61107B458f11eCC169A019b764", "latest"))
