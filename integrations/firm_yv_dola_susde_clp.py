from typing import List, Optional, Set
from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from constants.firm import FIRM_YV_SUSDE_DOLA_CLP_DEPLOYMENT_BLOCK, YV_SUSDE_DOLA_ADDRESS, YV_SUSDE_DOLA_CLP_MARKET_ADDRESS
from utils.firm import get_firm_market_participants, get_firm_user_balance, get_yearn_vault_v2_contract
from utils.web3_utils import w3, call_with_retry


class Firm(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.FIRM_YV_SUSDE_DOLA_CLP,
            FIRM_YV_SUSDE_DOLA_CLP_DEPLOYMENT_BLOCK,
            Chain.ETHEREUM,
            [],
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        balance = get_firm_user_balance(user, YV_SUSDE_DOLA_CLP_MARKET_ADDRESS, block)
        # Yearn-specific logic
        yearn_vault_v2_contract = get_yearn_vault_v2_contract(YV_SUSDE_DOLA_ADDRESS)
        # get the price_per_share to then get the underlying lp balance
        price_per_share = call_with_retry(
            yearn_vault_v2_contract.functions.pricePerShare(),
            block,
        )
        return balance / 1e18 * price_per_share / 1e18

    def get_participants(
        self,
        blocks: Optional[List[int]],
    ) -> Set[str]:
        return get_firm_market_participants(FIRM_YV_SUSDE_DOLA_CLP_DEPLOYMENT_BLOCK, YV_SUSDE_DOLA_CLP_MARKET_ADDRESS)


if __name__ == "__main__":
    firm = Firm()
    participants = firm.get_participants(None)
    print("participants", participants)
    currentBlock = w3.eth.get_block_number()
    if len(participants) > 0:
        print(firm.get_balance(list(participants)[len(participants) - 1], currentBlock))
