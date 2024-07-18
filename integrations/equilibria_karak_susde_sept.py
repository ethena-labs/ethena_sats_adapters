from constants.integration_ids import IntegrationID
from utils.equilibria import EquilibriaIntegration
from constants.equilibria import Karak_sUSDe_SEPT, Karak_sUSDe_SEPT_ID, Karak_sUSDe_SEPT_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.equilibria import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    equilibria_integration = EquilibriaIntegration(
        IntegrationID.EQUILIBRIA_Karak_SUSDE_SEPT_SEPT,
        Karak_sUSDe_SEPT_DEPLOYMENT_BLOCK,
        Karak_sUSDe_SEPT,
        Karak_sUSDe_SEPT_ID,
        Chain.ETHEREUM,
        20,
        1,
        [PENDLE_LOCKER_ETHEREUM]

    )

    print(equilibria_integration.get_participants())
    print(equilibria_integration.get_balance(list(equilibria_integration.get_participants())[0], "latest"))
