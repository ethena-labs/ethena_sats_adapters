from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from constants.summary_columns import SummaryColumn
from constants.lendle import LENDLE_SUSDE_DEPLOYMENT_BLOCK
from utils.web3_utils import w3_mantle, fetch_events_logs_with_retry, call_with_retry
from utils.lendle import lendle_susde_contract


class LendleIntegration(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.LENDLE_SUSDE_LPT,
            LENDLE_SUSDE_DEPLOYMENT_BLOCK,
            Chain.MANTLE,
            [SummaryColumn.LENDLE_MANTLE_SHARDS],
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int | str) -> float:
        bal = call_with_retry(
            lendle_susde_contract.functions.balanceOf(user),
            block,
        )
        if bal == 0:
            return 0

        return round((bal / 10**18), 4)

    # Important: This function should only be called once and should cache the results by setting self.participants
    def get_participants(self, blocks: list[int] | None) -> set[str]:
        page_size = 1900
        start_block = LENDLE_SUSDE_DEPLOYMENT_BLOCK
        target_block = w3_mantle.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"Lendle users from {start_block} to {to_block}",
                lendle_susde_contract.events.Transfer(),
                start_block,
                to_block,
            )
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
            start_block += page_size

        return set(all_users)


if __name__ == "__main__":
    lendle_integration = LendleIntegration()
    participants = lendle_integration.get_participants(None)
    print(participants)
    print(lendle_integration.get_balance(list(participants)[0], "latest"))
