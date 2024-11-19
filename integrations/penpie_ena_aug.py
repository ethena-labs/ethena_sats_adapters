from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import ENA29AUG2024_PRT, ENA29AUG2024_PRT_DEPLOYMENT_BLOCK
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_ENA29AUG2024_LPT,
        ENA29AUG2024_PRT_DEPLOYMENT_BLOCK,
        ENA29AUG2024_PRT,
        Chain.ETHEREUM,
        30,
        1,
        {PENDLE_LOCKER_ETHEREUM},
    )
    # print(penpie_integration.get_participants())
    print(
        penpie_integration.get_balance(
            "0xb60c9094FF0DFfF6aA266063A4C176B00Ad07fE8", "latest"
        )
    )
