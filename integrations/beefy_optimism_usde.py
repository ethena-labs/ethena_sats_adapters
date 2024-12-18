from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from utils.beefy import BeefyIntegration

if __name__ == "__main__":
    beefy_integration = BeefyIntegration(
        IntegrationID.BEEFY_OPTIMISM_USDE, 38082415, Chain.OPTIMISM
    )
    print(beefy_integration.get_participants(None))
    print(
        beefy_integration.get_balance(
            list(beefy_integration.get_participants(None))[0], 106819558
        )
    )
