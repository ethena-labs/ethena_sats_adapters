from constants.integration_ids import IntegrationID
from utils.equilibria import EquilibriaIntegration
from constants.equilibria import SUSDE_SEPT, SUSDE_SEPT_ID, SUSDE_SEPT_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.equilibria import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    equilibria_integration = EquilibriaIntegration(
        IntegrationID.EQUILIBRIA_SUSDE_SEPT_LPT,
        SUSDE_SEPT_DEPLOYMENT_BLOCK,
        SUSDE_SEPT,
        SUSDE_SEPT_ID,
        Chain.ETHEREUM,
        20,
        1,
        [PENDLE_LOCKER_ETHEREUM]

    )

    print(equilibria_integration.get_participants())
    print(equilibria_integration.get_balance(list(equilibria_integration.get_participants())[0], "latest"))
