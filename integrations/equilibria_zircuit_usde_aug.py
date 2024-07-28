from constants.integration_ids import IntegrationID
from utils.equilibria import EquilibriaIntegration
from constants.equilibria import Zircuit_USDe_AUG, Zircuit_USDe_AUG_ID, Zircuit_USDe_AUG_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.equilibria import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    equilibria_integration = EquilibriaIntegration(
        IntegrationID.EQUILIBRIA_Zircuit_USDE_AUG_LPT,
        Zircuit_USDe_AUG_DEPLOYMENT_BLOCK,
        Zircuit_USDe_AUG,
        Zircuit_USDe_AUG_ID,
        Chain.ETHEREUM,
        20,
        1,
        [PENDLE_LOCKER_ETHEREUM]

    )

    print(equilibria_integration.get_participants())
    print(equilibria_integration.get_balance(list(equilibria_integration.get_participants())[0], "latest"))
