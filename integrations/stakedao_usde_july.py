from integrations.integration_ids import IntegrationID
from utils.stakedao import StakeDAOIntegration
from constants.stakedao import USDE_JULY, USDE_JULY_DEPLOYMENT_BLOCK

if __name__ == "__main__":
    stakedao_integration = StakeDAOIntegration(
        IntegrationID.STAKEDAO_USDE_JULY_LPT,
        USDE_JULY_DEPLOYMENT_BLOCK,
        USDE_JULY,
    )
    print(stakedao_integration.get_participants())
