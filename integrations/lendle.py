from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.summary_columns import SummaryColumn
from constants.lendle import LENDLE_DEPLOYMENT_BLOCK
from utils.web3_utils import w3_mantle, fetch_events_logs_with_retry, call_with_retry
from utils.lendle import lendle_usde_contract

class LendleIntegration(
    Integration
):
    def __init__(self):
        super().__init__(
            IntegrationID.LENDLE_USDE_LP,
            LENDLE_DEPLOYMENT_BLOCK,
            Chain.MANTLE,
            [SummaryColumn.LENDLE_MANTLE_SHARDS],  # TODO: Optional, change None to a list of SummaryColumn enums that this protocol should be associated with, see Pendle grouping example
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        bal = call_with_retry(
            lendle_usde_contract.balanceOf(user),
            block,
        )
        if bal == 0:
            return 0

        print(
            f"lendle_bal: {bal}"
        )

        return round((bal / 10**18), 4)

    # Important: This function should only be called once and should cache the results by setting self.participants
    def get_participants(self) -> list:
        page_size = 1900
        start_block = LENDLE_DEPLOYMENT_BLOCK
        target_block = w3_mantle.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"Lendle users from {start_block} to {to_block}",
                lendle_usde_contract.events.Transfer(),
                start_block,
                to_block,
            )
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
            start_block += page_size

        all_users = list(all_users)
        self.participants = all_users
        return all_users


if __name__ == "__main__":
    # TODO: Write simple tests for the integration
    example_integration = LendleIntegration()
    print(example_integration.get_participants())
    print(
        example_integration.get_balance(
            list(example_integration.get_participants())[0], LENDLE_DEPLOYMENT_BLOCK
        )
    )
