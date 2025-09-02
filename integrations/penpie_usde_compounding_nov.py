from integrations.integration_ids import IntegrationID
from utils.penpieCompound import PENPIECompoundIntegration
from constants.penpie import USDE_COMPOUNDING_27NOV2025, USDE_COMPOUNDING_27NOV2025_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIECompoundIntegration(
        IntegrationID.PENPIE_USDE_COMPOUNDING_27NOV2025_LPT,
        USDE_COMPOUNDING_27NOV2025_DEPLOYMENT_BLOCK,
        USDE_COMPOUNDING_27NOV2025,
        Chain.ETHEREUM,
        60,
        1,
        {PENDLE_LOCKER_ETHEREUM},
    )
    print(penpie_integration.get_participants(None))
    # print(penpie_integration.get_balance("0xe95176DF139a93D706655B32Df087a97e212B78E"))
