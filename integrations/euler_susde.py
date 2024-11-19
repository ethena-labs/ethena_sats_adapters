import json
from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from constants.euler import SUSDE_VAULT_ADDRESS
from constants.merchantmoe import DEAD_ADDRESS, ZERO_ADDRESS
from integrations.integration import Integration
from utils.web3_utils import (
    fetch_events_logs_with_retry,
    call_with_retry,
    w3,
)
from web3 import Web3

with open("abi/euler_evault.json") as f:
    evault_abi = json.load(f)


class EulerIntegration(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.EULER_SUSDE,
            20529207,
            Chain.ETHEREUM,
            None,
            5,
            1,
            None,
            None,
        )
        self.vault_contract = w3.eth.contract(
            address=SUSDE_VAULT_ADDRESS, abi=evault_abi
        )

    def get_balance(self, user: str, block: int) -> float:
        try:
            etoken_balance = call_with_retry(
                self.vault_contract.functions.balanceOf(user), block
            )
            if etoken_balance == 0:
                return 0
            asset_balance = call_with_retry(
                self.vault_contract.functions.convertToAssets(etoken_balance), block
            )
        except Exception as ex:
            print("Error getting balance for user %s: %s", user, ex)
            return 0

        return round(asset_balance / 1e18, 4)

    def get_participants(self) -> list:
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
                if from_address != ZERO_ADDRESS and from_address != DEAD_ADDRESS:
                    all_users.add(Web3.to_checksum_address(from_address))
                if to_address != ZERO_ADDRESS and to_address != DEAD_ADDRESS:
                    all_users.add(Web3.to_checksum_address(to_address))

            start += batch_size

        return all_users


if __name__ == "__main__":
    example_integration = EulerIntegration()
    participants = example_integration.get_participants()
    print(participants)
    print(example_integration.get_balance(participants[0], 20677865))
