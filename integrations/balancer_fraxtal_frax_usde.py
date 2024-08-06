from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.balancer import (
    BALANCER_FRAXTAL_DEPLOYMENT_BLOCK,
    BALANCER_FRAXTAL_FRAX_USDE_GAUGE,
)
import json
from utils.web3_utils import (
    call_with_retry,
    w3_fraxtal,
)
from utils.balancer import fetch_participants

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


class BalancerIntegration(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.BALANCER_FRAXTAL_FRAX_USDE,
            BALANCER_FRAXTAL_DEPLOYMENT_BLOCK,
            Chain.FRAXTAL,
            None,
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        gauge_contract = w3_fraxtal.eth.contract(
            address=BALANCER_FRAXTAL_FRAX_USDE_GAUGE, abi=erc20_abi
        )

        gauge_total_supply = call_with_retry(
            gauge_contract.functions.totalSupply(),
            block,
        )

        gauge_user_balance = call_with_retry(
            gauge_contract.functions.balanceOf(user),
            block,
        )

        user_share = gauge_user_balance * 100 / gauge_total_supply

        return user_share

    def get_participants(self) -> list:
        self.participants = fetch_participants(BALANCER_FRAXTAL_DEPLOYMENT_BLOCK)
        return self.participants


if __name__ == "__main__":
    balancer = BalancerIntegration()
    print(balancer.get_participants())
    print(balancer.get_balance(list(balancer.get_participants())[0], 8000000))
