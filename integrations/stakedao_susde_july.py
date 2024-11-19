from integrations.integration_ids import IntegrationID
from utils.stakedao import StakeDAOIntegration
from constants.stakedao import SUSDE_JULY, SUSDE_JULY_DEPLOYMENT_BLOCK

if __name__ == "__main__":
    stakedao_integration = StakeDAOIntegration(
        IntegrationID.STAKEDAO_SUSDE_JULY_LPT,
        SUSDE_JULY_DEPLOYMENT_BLOCK,
        SUSDE_JULY,
    )
    print(stakedao_integration.get_participants(None))
