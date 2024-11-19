from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import SUSDE_JULY, SUSDE_JULY_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_SUSDE_JULY_LPT,
        SUSDE_JULY_DEPLOYMENT_BLOCK,
        SUSDE_JULY,
        Chain.ETHEREUM,
        20,
        1,
        [PENDLE_LOCKER_ETHEREUM],
    )
    # print(penpie_integration.get_participants())
    print(
        penpie_integration.get_balance(
            "0x79E40Ab4BAc23E2910C03E2Fc24819fE498A9491", "latest"
        )
    )
