from integrations.integration_ids import IntegrationID
from utils.splice import SpliceIntegration

if __name__ == "__main__":
    integration = SpliceIntegration(IntegrationID.SPLICE_USDE_LPT)
    print(integration.get_participants(None))
    print(integration.get_balance(list(integration.get_participants(None))[0]))
