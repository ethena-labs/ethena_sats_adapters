from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.balancer import get_user_balance, get_token_supply, get_token_holders
from constants.balancer import (
    BALANCER_FRAXTAL_DEPLOYMENT_BLOCK,
    BALANCER_FRAXTAL_FRAX_USDE_GAUGE,
    BALANCER_FRAXTAL_FRAX_USDE_AURA,
    AURA_VOTER_PROXY,
)


class BalancerIntegration(Integration):
    def __init__(
        self,
        chain: Chain,
        start_block: int,
        integration_id: IntegrationID,
        gauge_address: str,
        aura_address: str,
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            None,
            20,
            1,
            None,
            None,
        )

        self.gauge_address = gauge_address
        self.aura_address = aura_address

    def get_balance(self, user: str, block: int) -> float:
        gauge_balance = get_user_balance(self.chain, user, self.gauge_address, block)
        aura_balance = get_user_balance(self.chain, user, self.aura_address, block)

        gauge_supply = get_token_supply(self.chain, self.gauge_address, block)
        aura_supply = get_token_supply(self.chain, self.aura_address, block)

        aura_voter_balance = get_user_balance(
            self.chain, AURA_VOTER_PROXY[self.chain], self.gauge_address, block
        )

        # Avoid double-counting of Gauge tokens held by Aura Voter Proxy
        total_supply = gauge_supply + aura_supply - aura_voter_balance
        user_balance = gauge_balance + aura_balance

        return user_balance / total_supply

    def get_participants(self) -> list:
        gauge_holders = get_token_holders(
            self.chain, self.gauge_address, self.start_block
        )
        aura_holders = get_token_holders(
            self.chain, self.aura_address, self.start_block
        )
        self.participants = set(aura_holders + gauge_holders)
        return self.participants


if __name__ == "__main__":
    balancer = BalancerIntegration(
        Chain.FRAXTAL,
        BALANCER_FRAXTAL_DEPLOYMENT_BLOCK,
        IntegrationID.BALANCER_FRAXTAL_FRAX_USDE,
        BALANCER_FRAXTAL_FRAX_USDE_GAUGE,
        BALANCER_FRAXTAL_FRAX_USDE_AURA,
    )
    print(balancer.get_participants())
    print(balancer.get_balance(list(balancer.participants)[0], "latest"))
