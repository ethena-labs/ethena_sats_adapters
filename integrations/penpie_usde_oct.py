from constants.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import USDe_24OCT2024, USDe_24OCT2024_DEPLOYMENT_BLOCK   
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_USDe_24OCT2024_LPT,
        USDe_24OCT2024_DEPLOYMENT_BLOCK,
        USDe_24OCT2024,
        Chain.ETHEREUM,
        25,
        1,
        [PENDLE_LOCKER_ETHEREUM]

    )
    # print(penpie_integration.get_participants())
    print(penpie_integration.get_balance("0x79E40Ab4BAc23E2910C03E2Fc24819fE498A9491", "latest"))