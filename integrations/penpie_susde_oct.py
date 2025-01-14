from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import sUSDE_24OCT2024, sUSDE_24OCT2024_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_sUSDE_24OCT2024_LPT,
        sUSDE_24OCT2024_DEPLOYMENT_BLOCK,
        sUSDE_24OCT2024,
        Chain.ETHEREUM,
        20,
        1,
        {PENDLE_LOCKER_ETHEREUM},
    )
    print(penpie_integration.get_participants(None))
    # print(penpie_integration.get_balance("0xe95176DF139a93D706655B32Df087a97e212B78E", "latest"))
