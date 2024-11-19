from utils.web3_utils import W3_BY_CHAIN
from integrations.integration_ids import IntegrationID
from utils.allstake import AllstakeIntegration


if __name__ == "__main__":
    integration = AllstakeIntegration(IntegrationID.ALLSTAKE_USDE)
    current_block = W3_BY_CHAIN[integration.chain]["w3"].eth.get_block_number()

    participants = integration.get_participants()
    print("Get Participants:")
    print(participants)
    print("Get Balances of All Participants:")
    for participant in participants:
        print(participant, integration.get_balance(participant, current_block))
