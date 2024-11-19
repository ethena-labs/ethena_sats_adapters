from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import sUSDe26SEP2024_PRT, sUSDe26SEP2024_PRT_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_sUSDe26SEP2024_LPT,
        sUSDe26SEP2024_PRT_DEPLOYMENT_BLOCK,
        sUSDe26SEP2024_PRT,
        Chain.ETHEREUM,
        20,
        1,
        [PENDLE_LOCKER_ETHEREUM],
    )
    # print(penpie_integration.get_participants())
    print(
        penpie_integration.get_balance(
            "0xe95176DF139a93D706655B32Df087a97e212B78E", "latest"
        )
    )
