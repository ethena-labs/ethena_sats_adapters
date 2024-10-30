from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.web3_utils import call_with_retry, W3_BY_CHAIN
from utils.fluid import vaultResolver_contract, vaultFactory_contract

class FluidIntegration(
    Integration
):  # TODO: Change FluidIntegration to the name of the protocol
    def __init__(self):
        super().__init__(
            IntegrationID.FLUID,  # TODO: Change EXAMPLE to the name of the protocol
            21016131,  # TODO: Change 20000000 to the start block of the protocol when events/balances should first be tracked
            Chain.ETHEREUM,  # TODO: Change ETHEREUM to the chain of the protocol
            None,  # TODO: Optional, change None to a list of SummaryColumn enums that this protocol should be associated with, see Pendle grouping example
            20,  # TODO: Change 20 to the sats multiplier for the protocol that has been agreed upon
            1,  # TODO: Almost always 1, optionally change to a different value if an adjustment needs to be applied to balances
            None,  # TODO: Optional, change None to the end block of the protocol when events/balances should stop being tracked
            None,  # TODO: Optional, change None to a function that takes a block number and returns the reward multiplier for that block if it has or will change over time
        )

    # TODO: Implement function for getting a given user's balance at a given block
    def get_balance(self, user: str, block: int) -> float:
        balance = 0
        try:
            userPositions, _ = call_with_retry(vaultResolver_contract.functions.positionsByUser(user), block)
            print(userPositions)
            for userPosition in userPositions:
                balance += userPosition[9]
            return balance/1e18
        except Exception as e:
            return 0


    # TODO: Implement function for getting all participants of the protocol, ever
    # Important: This function should only be called once and should cache the results by setting self.participants
    def get_participants(self) -> list:
        participants = []
        current_block = W3_BY_CHAIN[self.chain]["w3"].eth.get_block_number()
        try:
            current_block = W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.get_block_number()
            total_nfts = call_with_retry(vaultResolver_contract.functions.totalPositions(), current_block)
            for i in range(1, total_nfts + 1):
                owner = call_with_retry(vaultFactory_contract.functions.ownerOf(i), current_block)
                if owner not in participants:
                    participants.append(owner)
        except Exception as e:
            print(f"Error: {str(e)}")
        return participants


if __name__ == "__main__":
    # TODO: Write simple tests for the integration
    example_integration = FluidIntegration()
    # print(example_integration.get_participants())
    print(
        example_integration.get_balance("0x169dC0999f4dD957EbcB68a7A8AFfe87c57C4faE", 21079685)
    )
