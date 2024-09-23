from constants.chains import Chain
from constants.integration_ids import IntegrationID
from utils.beefy import BeefyIntegration

if __name__ == "__main__":
    beefy_integration = BeefyIntegration(
        IntegrationID.BEEFY_FRAXTAL_USDE,
        2366784,
        Chain.FRAXTAL
    )
    print(beefy_integration.get_participants())
    print(
        beefy_integration.get_balance(
            list(beefy_integration.get_participants())[0], 2466784
        )
    )
