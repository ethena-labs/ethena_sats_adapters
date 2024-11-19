from utils.web3_utils import W3_BY_CHAIN
import logging

from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from utils.lyra import (
    get_vault_users,
    get_effective_balance,
    get_exchange_users,
    get_exchange_balance,
)
from constants.lyra import (
    LYRA_CONTRACTS_AND_START_BY_TOKEN,
    LyraVaultDetails,
    DetailType,
)


class LyraIntegration(Integration):
    def __init__(self, integration_id: IntegrationID):
        self.vault_data: LyraVaultDetails = LYRA_CONTRACTS_AND_START_BY_TOKEN[
            integration_id
        ]

        print(self.vault_data)

        super().__init__(
            integration_id,
            self.vault_data["start"],
            self.vault_data["chain"],
            None,
            5,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        if self.vault_data["detail_type"] == DetailType.Vault:
            return get_effective_balance(
                user,
                block,
                self.vault_data["integration_token"],
                self.vault_data["bridge"],
                self.vault_data["vault_token"],
                W3_BY_CHAIN[example_integration.chain]["w3"].eth.get_block(block)[
                    "timestamp"
                ],
            )

        else:
            return get_exchange_balance(user, block)

    def get_participants(self) -> list:
        logging.info(
            f"[{self.integration_id.get_description()}] Getting participants..."
        )
        if self.vault_data["detail_type"] == DetailType.Vault:
            self.participants = get_vault_users(
                self.start_block,
                self.vault_data["page_size"],
                self.vault_data["vault_token"],
                self.chain,
            )
        else:
            self.participants = get_exchange_users()

        return self.participants


if __name__ == "__main__":
    example_integration = LyraIntegration(IntegrationID.LYRA_SUSDE_BULL_MAINNET)
    current_block = W3_BY_CHAIN[example_integration.chain]["w3"].eth.get_block_number()

    print("Found Lyra Participants:")
    print(example_integration.get_participants())
    print("Found Balance of First Participant:")
    print(
        example_integration.get_balance(
            list(example_integration.participants)[0], current_block
        )
    )
