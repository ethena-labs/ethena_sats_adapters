from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import rsUSDe_26SEP2024, rsUSDe_26SEP2024_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_rsUSDe_26SEP2024_LPT,
        rsUSDe_26SEP2024_DEPLOYMENT_BLOCK,
        rsUSDe_26SEP2024,
        Chain.ETHEREUM,
        10,
        1,
        {PENDLE_LOCKER_ETHEREUM},
    )
    print(penpie_integration.get_participants(None))
