from constants.integration_ids import IntegrationID
from utils.equilibria import EquilibriaIntegration
from constants.equilibria import USDE_EXPIRY, USDE_EXPIRY_ID, USDE_EXPIRY_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.equilibria import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    equilibria_integration = EquilibriaIntegration(
        IntegrationID.EQUILIBRIA_USDE_LPT_EXPIRY,
        USDE_EXPIRY_DEPLOYMENT_BLOCK,
        USDE_EXPIRY,
        USDE_EXPIRY_ID,
        Chain.ETHEREUM,
        20,
        1,
        [PENDLE_LOCKER_ETHEREUM]
    )

    print(equilibria_integration.get_participants())
    print(equilibria_integration.get_balance(list(equilibria_integration.get_participants())[0], "latest"))
