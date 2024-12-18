from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import ENA_31OCT2024, ENA_31OCT2024_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_ENA_31OCT2024_LPT,
        ENA_31OCT2024_DEPLOYMENT_BLOCK,
        ENA_31OCT2024,
        Chain.ETHEREUM,
        30,
        1,
        {PENDLE_LOCKER_ETHEREUM},
    )
    # print(penpie_integration.get_participants())
    print(
        penpie_integration.get_balance(
            "0x9EF171A8C62Eea6455830Bde5de99Db5A7cA5119", "latest"
        )
    )
