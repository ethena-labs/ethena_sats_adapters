from typing import List, Optional, Set
from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from constants.firm import FIRM_SUSDE_DOLA_CLP_DEPLOYMENT_BLOCK, SUSDE_DOLA_CLP_MARKET_ADDRESS
from utils.firm import get_firm_market_participants, get_firm_user_balance
from utils.web3_utils import w3


class Firm(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.FIRM_SUSDE_DOLA_CLP,
            FIRM_SUSDE_DOLA_CLP_DEPLOYMENT_BLOCK,
            Chain.ETHEREUM,
            [],
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        balance = get_firm_user_balance(user, SUSDE_DOLA_CLP_MARKET_ADDRESS, block)
        return balance / 1e18

    def get_participants(
        self,
        blocks: Optional[List[int]],
    ) -> Set[str]:
        return get_firm_market_participants(FIRM_SUSDE_DOLA_CLP_DEPLOYMENT_BLOCK, SUSDE_DOLA_CLP_MARKET_ADDRESS)


if __name__ == "__main__":
    firm = Firm()
    participants = firm.get_participants(None)
    print("participants", participants)
    currentBlock = w3.eth.get_block_number()
    if len(participants) > 0:
        print(firm.get_balance(list(participants)[len(participants) - 1], currentBlock))
