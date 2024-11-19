from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import sUSDe25APR2024_PRT, sUSDe25APR2024_PRT_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_sUSDe25APR2024_LPT,
        sUSDe25APR2024_PRT_DEPLOYMENT_BLOCK,
        sUSDe25APR2024_PRT,
        Chain.ETHEREUM,
        20,
        1,
        {PENDLE_LOCKER_ETHEREUM},
    )
    # print(penpie_integration.get_participants())
    print(
        penpie_integration.get_balance(
            "0x48553662B61D9B246206fdC5Ee06C643ED85cb00", "latest"
        )
    )
