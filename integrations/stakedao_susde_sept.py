from constants.integration_ids import IntegrationID
from utils.stakedao import StakeDAOIntegration
from constants.stakedao import SUSDE_SEPT, SUSDE_SEPT_DEPLOYMENT_BLOCK  

if __name__ == "__main__":
    stakedao_integration = StakeDAOIntegration(
        IntegrationID.STAKEDAO_SUSDE_SEPT_LPT,
        SUSDE_SEPT_DEPLOYMENT_BLOCK,
        SUSDE_SEPT,
    )
    print(stakedao_integration.get_participants())
