from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration


class ProtocolNameIntegration(
    Integration
):  # TODO: Change ProtocolNameIntegration to the name of the protocol
    def __init__(self):
        super().__init__(
            IntegrationID.EXAMPLE,  # TODO: Change EXAMPLE to the name of the protocol
            20000000,  # TODO: Change 20000000 to the start block of the protocol when events/balances should first be tracked
            Chain.ETHEREUM,  # TODO: Change ETHEREUM to the chain of the protocol
            None,  # TODO: Optional, change None to a list of SummaryColumn enums that this protocol should be associated with, see Pendle grouping example
            20,  # TODO: Change 20 to the sats multiplier for the protocol that has been agreed upon
            1,  # TODO: Almost always 1, optionally change to a different value if an adjustment needs to be applied to balances
            None,  # TODO: Optional, change None to the end block of the protocol when events/balances should stop being tracked
            None,  # TODO: Optional, change None to a function that takes a block number and returns the reward multiplier for that block if it has or will change over time
        )

    # TODO: Implement function for getting a given user's balance at a given block
    def get_balance(self, user: str, block: int) -> float:
        pass

    # TODO: Implement function for getting all participants of the protocol, ever
    # Important: This function should only be called once and should cache the results by setting self.participants
    def get_participants(self) -> list:
        pass


if __name__ == "__main__":
    # TODO: Write simple tests for the integration
    example_integration = ProtocolNameIntegration()
    print(example_integration.get_participants())
    print(
        example_integration.get_balance(
            list(example_integration.get_participants())[0], 20000001
        )
    )
