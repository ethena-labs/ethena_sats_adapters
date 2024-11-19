from integrations.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import (
    Karak_sUSDe_26SEP2024_PRT,
    Karak_sUSDe_26SEP2024_PRT_DEPLOYMENT_BLOCK,
)
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_Karak_sUSDe_26SEP2024_LPT,
        Karak_sUSDe_26SEP2024_PRT_DEPLOYMENT_BLOCK,
        Karak_sUSDe_26SEP2024_PRT,
        Chain.ETHEREUM,
        5,
        1,
        [PENDLE_LOCKER_ETHEREUM],
    )
    # print(penpie_integration.get_participants())
    print(
        penpie_integration.get_balance(
            "0xb873BCF80afA89c2A9e5182f5792d64a03Eb4311", "latest"
        )
    )
