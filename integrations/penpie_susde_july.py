from constants.integration_ids import IntegrationID
from utils.penpie import PENPIEIntegration
from constants.penpie import SUSDE_JULY, SUSDE_JULY_DEPLOYMENT_BLOCK   

if __name__ == "__main__":
    penpie_integration = PENPIEIntegration(
        IntegrationID.STAKEDAO_SUSDE_JULY_LPT,
        SUSDE_JULY_DEPLOYMENT_BLOCK,
        SUSDE_JULY,
    )
    # print(penpie_integration.get_participants())
    print(penpie_integration.get_balance(0x581cAfb44a325BaeA297Ee4a0a327B839999128C, "latest"))