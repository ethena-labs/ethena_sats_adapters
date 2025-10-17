from typing import List, Optional, Set
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID

from utils.berachain import get_pool_token_holders, get_user_balance
from constants.berachain import BERACHAIN_CONFIGS


class BerachainBEXIntegration(Integration):

    def __init__(self, integration_id: IntegrationID):
        config = BERACHAIN_CONFIGS[integration_id]
        self.start_block = config.start_block
        self.pool = config.pool
        self.reward_vault = config.reward_vault
    
    def get_balance(self, user: str, block: int | str = "latest") -> float:
        pool_balance = get_user_balance(user, self.pool, block)

        reward_vault_balance = 0 if self.reward_vault is None else get_user_balance(user, self.reward_vault, block)

        return pool_balance + reward_vault_balance
    
    def get_participants(
        self,
        blocks: Optional[List[int]],
    ) -> Set[str]:
        return get_pool_token_holders(self.pool, self.reward_vault, self.start_block)

if __name__ == "__main__":
    berachain_bex_integration = BerachainBEXIntegration(
        IntegrationID.BERACHAIN_LP_sUSDe_USDe_HONEY_POOL
    )
    partecipants = berachain_bex_integration.get_participants(None)
    print(partecipants)
    for p in partecipants:

        print(p, 
            berachain_bex_integration.get_balance(
                p, 11905710
            )
        )
