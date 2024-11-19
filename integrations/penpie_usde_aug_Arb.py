from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import USDE_ARB_AUG2024, USDE_ARB_AUG2024_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ARBITRUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_USDE_ARB_AUG2024_LPT,
        USDE_ARB_AUG2024_DEPLOYMENT_BLOCK,
        USDE_ARB_AUG2024,
        Chain.ARBITRUM,
        20,
        1,
        {PENDLE_LOCKER_ARBITRUM},
    )
    print(penpie_integration.get_participants(None))
    # print(penpie_integration.get_balance("0xe95176DF139a93D706655B32Df087a97e212B78E", "latest"))
