from constants.chains import Chain
from constants.integration_ids import IntegrationID
from constants.integration_token import Token
from constants.summary_columns import SummaryColumn
from models.integration import Integration


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

    def get_id(self) -> IntegrationID:
        return self.integration_id

    def get_token(self) -> Token:
        return self.integration_id.get_token()

    def get_description(self) -> str:
        return self.integration_id.get_description()

    def get_col_name(self) -> str:
        return self.integration_id.get_column_name()

    def get_chain(self) -> Chain:
        return self.chain

    def get_summary_cols(self) -> list[SummaryColumn]:
        return self.summary_cols

    def get_reward_multiplier(self, block: int) -> int:
        if self.reward_multiplier_func is not None:
            return self.reward_multiplier_func(block)
        return self.reward_multiplier

    def get_balance_multiplier(self) -> int:
        return self.balance_multiplier

    def get_start_block(self) -> int:
        return self.start_block

    def get_end_block(self) -> int:
        if self.end_block is None:
            return (
                2**31 - 1
            )  # if no end block is specified, return the maximum possible block number
        return self.end_block

    def is_user_a_participant(self, user: str) -> bool:
        if self.participants is None:
            self.get_participants()
        return user in self.participants
    

if __name__ == "__main__":
    # TODO: Write simple tests for the integration
    example_integration = ProtocolNameIntegration()
    print(example_integration.get_participants())
    print(example_integration.get_balance(list(example_integration.get_participants())[0], 20000001))
