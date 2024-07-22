from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.web3_utils import call_with_retry, W3_BY_CHAIN
from utils.kinto import get_kinto_susde_contract, fetch_participants
from constants.kinto import KINTO_SUSDE_DEPLOYMENT_BLOCK
import logging

class KintoSUDEIntegration(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.KINTO_SUSDE_LP,
            KINTO_SUSDE_DEPLOYMENT_BLOCK,
            Chain.KINTO,
            None,
            5,
            1,
            None,
            None,
        )
        self.web3 = W3_BY_CHAIN["kinto"]["w3"]
        self.contract = get_kinto_susde_contract(self.web3)

    def get_balance(self, user: str, block: int) -> float:
        balance = call_with_retry(
            self.contract.functions.balanceOf(user),
            block=block
        )
        return float(self.web3.from_wei(balance, 'ether'))

    def get_participants(self) -> list:
        if self.participants is not None:
            return self.participants
        
        self.participants = fetch_participants(self.contract, self.start_block)
        return self.participants


if __name__ == "__main__":
    example_integration = KintoSUDEIntegration()
    print("KintoSUDEIntegration")
    # Example call to get_balance (replace with a valid user address and block number)
    participants = example_integration.get_participants()
    print(f"Example get_participantParticipants found: {len(participants)}")
    print(f"Balance for {participants[0]}: {example_integration.get_balance(participants[0], 'latest')} sUSDE")
