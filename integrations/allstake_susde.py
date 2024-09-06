from utils.web3_utils import W3_BY_CHAIN
from constants.integration_ids import IntegrationID
from utils.allstake import AllstakeIntegration


if __name__ == "__main__":
    integration = AllstakeIntegration(IntegrationID.ALLSTAKE_SUSDE)
    current_block = W3_BY_CHAIN[integration.chain]["w3"].eth.get_block_number()

    print("Get Participants:")
    print(integration.get_participants())
    print("Get Balance of First Participant:")
    print(integration.get_balance(list(integration.participants)[0], current_block))
