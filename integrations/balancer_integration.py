from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.balancer import get_user_balance, get_token_supply, get_token_holders
from constants.balancer import AURA_VOTER_PROXY, INTEGRATION_CONFIGS


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

        self.gauge_address = config.gauge_address
        self.aura_address = config.aura_address

    def get_balance(self, user: str, block: int) -> float:
        """
        Retrieve the share of Balancer Pool Tokens (BPTs) held by a specific user.

        This method calculates the user's share of the total supply of BPTs
        staked in Balancer gauges and Aura Finance.

        Note that the Aura Voter Proxy contract is used to avoid double-counting
        of gauge tokens held by Aura Finance.
        """
        gauge_balance = get_user_balance(self.chain, user, self.gauge_address, block)
        aura_balance = (
            get_user_balance(self.chain, user, self.aura_address, block)
            if self.aura_address
            else 0
        )

        gauge_supply = get_token_supply(self.chain, self.gauge_address, block)
        aura_supply = (
            get_token_supply(self.chain, self.aura_address, block)
            if self.aura_address
            else 0
        )

        aura_voter_balance = (
            get_user_balance(
                self.chain, AURA_VOTER_PROXY[self.chain], self.gauge_address, block
            )
            if self.aura_address
            else 0
        )

        # Avoid double-counting of Gauge tokens held by Aura Voter Proxy
        total_supply = gauge_supply + aura_supply - aura_voter_balance
        user_balance = gauge_balance + aura_balance

        return user_balance / total_supply

    def get_participants(self) -> list:
        """
        Retrieve the set of all unique participants who have staked Balancer Pool Tokens (BPTs).

        This method identifies all addresses that have staked their BPT either directly
        in Balancer gauges or via Aura Finance. Non-staked BPT holders are not included.
        """
        gauge_holders = get_token_holders(
            self.chain, self.gauge_address, self.start_block
        )
        aura_holders = (
            get_token_holders(self.chain, self.aura_address, self.start_block)
            if self.aura_address
            else []
        )
        self.participants = set(aura_holders + gauge_holders)
        return self.participants


if __name__ == "__main__":
    balancer = BalancerIntegration(IntegrationID.BALANCER_FRAXTAL_FRAX_USDE)
    print(balancer.get_participants())
    print(balancer.get_balance(list(balancer.participants)[0], "latest"))
