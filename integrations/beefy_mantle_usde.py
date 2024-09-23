from constants.chains import Chain
from constants.integration_ids import IntegrationID
from utils.beefy import BeefyIntegration

if __name__ == "__main__":
    beefy_integration = BeefyIntegration(
        IntegrationID.BEEFY_MANTLE_USDE,
        66470986,
        Chain.MANTLE
    )
    print(beefy_integration.get_participants())
    print(
        beefy_integration.get_balance(
            list(beefy_integration.get_participants())[0], 66480986
        )
    )
