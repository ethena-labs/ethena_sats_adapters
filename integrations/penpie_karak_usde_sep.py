from constants.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import Karak_USDE_26SEP2024_PRT, Karak_USDE_26SEP2024_PRT_DEPLOYMENT_BLOCK   
from constants.chains import Chain
from constants.penpie import PENDLE_LOCKER_ETHEREUM

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.PENPIE_Karak_USDE_26SEP2024_LPT,
        Karak_USDE_26SEP2024_PRT_DEPLOYMENT_BLOCK,
        Karak_USDE_26SEP2024_PRT,
        Chain.ETHEREUM,
        20,
        1,
        [PENDLE_LOCKER_ETHEREUM]

    )
    # print(penpie_integration.get_participants())
    print(penpie_integration.get_balance("0x404581FA706E4E0d649A40eA503f9bCee3D2d76c", "latest"))