from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import USDE_25SEP2025, USDE_25SEP2025_DEPLOYMENT_BLOCK, USDE_AUTOMARKET_25SEP2025
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_USDE_SEP2025_LPT,
        USDE_25SEP2025_DEPLOYMENT_BLOCK,
        USDE_25SEP2025,
        Chain.ETHEREUM,
        25,
        1,
        {PENDLE_LOCKER_ETHEREUM},
        USDE_AUTOMARKET_25SEP2025
    )
    # print(penpie_integration.get_participants())
    print(
        penpie_integration.get_balance(
            "0x79E40Ab4BAc23E2910C03E2Fc24819fE498A9491", "latest"
        )
    )
