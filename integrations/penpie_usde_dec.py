from constants.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import USDe_26DEC2024, USDe_26DEC2024_DEPLOYMENT_BLOCK   
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_USDe_26DEC2024_LPT,
        USDe_26DEC2024_DEPLOYMENT_BLOCK,
        USDe_26DEC2024,
        Chain.ETHEREUM,
        25,
        1,
        [PENDLE_LOCKER_ETHEREUM]

    )
    # print(penpie_integration.get_participants())
    print(penpie_integration.get_balance("0xe95176DF139a93D706655B32Df087a97e212B78E", "latest"))