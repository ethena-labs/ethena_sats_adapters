from integrations.integration_ids import IntegrationID
from utils.splice import SpliceIntegration

if __name__ == "__main__":
    integration = SpliceIntegration(IntegrationID.SPLICE_USDE_YT)
    print(integration.get_participants())
    print(integration.get_balance(list(integration.get_participants())[0]))
