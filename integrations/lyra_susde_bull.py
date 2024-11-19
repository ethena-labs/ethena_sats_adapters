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
                integration_token=self.vault_data["integration_token"],  # type: ignore
                bridge=self.vault_data["bridge"],  # type: ignore
                vault_token=self.vault_data["vault_token"],  # type: ignore
                timestamp=W3_BY_CHAIN[self.chain]["w3"].eth.get_block(block)[
                    "timestamp"
                ],
            )

        else:
            return get_exchange_balance(user, block)

    def get_participants(self, blocks: list[int] | None) -> set[str]:
        logging.info(
            f"[{self.integration_id.get_description()}] Getting participants..."
        )
        if self.vault_data["detail_type"] == DetailType.Vault:
            self.participants = get_vault_users(
                start_block=self.start_block,
                page_size=self.vault_data["page_size"],  # type: ignore
                vault_token=self.vault_data["vault_token"],  # type: ignore
                chain=self.chain,
            )
        else:
            self.participants = get_exchange_users()

        return set(self.participants)


if __name__ == "__main__":
    example_integration = LyraIntegration(IntegrationID.LYRA_SUSDE_BULL_MAINNET)
    current_block = W3_BY_CHAIN[example_integration.chain]["w3"].eth.get_block_number()

    print("Found Lyra Participants:")
    participants = example_integration.get_participants(None)
    print(participants)
    print("Found Balance of First Participant:")
    print(example_integration.get_balance(list(participants)[0], current_block))
