from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import (
    Zircuit_USDe27JUN2024_PRT,
    Zircuit_USDe27JUN2024_PRT_DEPLOYMENT_BLOCK,
)
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_Zircuit_USDe27JUN2024_LPT,
        Zircuit_USDe27JUN2024_PRT_DEPLOYMENT_BLOCK,
        Zircuit_USDe27JUN2024_PRT,
        Chain.ETHEREUM,
        25,
        1,
        {PENDLE_LOCKER_ETHEREUM},
    )
    # print(penpie_integration.get_participants())
    print(
        penpie_integration.get_balance(
            "0xC5FBC522B2C1Ff8A47c2b7BF947321C808be5e64", "latest"
        )
    )
