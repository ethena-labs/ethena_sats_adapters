import json
from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from constants.euler import USDE_VAULT_ADDRESS
from integrations.integration import Integration
from utils.web3_utils import (
    fetch_events_logs_with_retry,
    call_with_retry,
    w3,
)

with open("abi/euler_evault.json") as f:
    evault_abi = json.load(f)


class EulerIntegration(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.EULER_USDE,
            20529207,
            Chain.ETHEREUM,
            None,
            20,
            1,
            None,
            None,
        )

        self.vault_contract = w3.eth.contract(
            address=USDE_VAULT_ADDRESS, abi=evault_abi
        )

    def get_balance(self, user: str, block: int) -> float:
        try:
            etoken_balance = call_with_retry(
                self.vault_contract.functions.balanceOf(user), block
            )
            asset_balance = call_with_retry(
                self.vault_contract.functions.convertToAssets(etoken_balance), block
            )
        except Exception as ex:
            print("Error getting balance for user %s: %s", user, ex)

        return asset_balance

    def get_participants(self, blocks: list[int] | None) -> set[str]:
        if self.participants is not None:
            return self.participants

        all_users = set()
        start = self.start_block
        end = w3.eth.get_block_number()

        batch_size = 10000

        while start < end:
            current_batch_end = min(start + batch_size, end)
            transfers = fetch_events_logs_with_retry(
                f"Euler Vault {self.vault_contract}",
                self.vault_contract.events.Transfer(),
                start,
                current_batch_end,
            )

            for transfer in transfers:
                from_address = transfer["args"]["from"]
                to_address = transfer["args"]["to"]
                if from_address != "0x0000000000000000000000000000000000000000":
                    all_users.add(from_address)
                if to_address != "0x0000000000000000000000000000000000000000":
                    all_users.add(to_address)

            start += batch_size

        return all_users


if __name__ == "__main__":
    example_integration = EulerIntegration()
    participants = example_integration.get_participants(None)
    print(participants)
    print(example_integration.get_balance(list(participants)[0], 20677865))
