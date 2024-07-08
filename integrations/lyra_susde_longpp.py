from utils.web3_utils import W3_BY_CHAIN

from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.lyra import get_vault_users, get_effective_balance
from constants.lyra import LYRA_CONTRACTS_AND_START_BY_TOKEN, LyraVaultDetails


class LyraIntegration(Integration):
    def __init__(self, integration_id: IntegrationID):
        vault_data: LyraVaultDetails = LYRA_CONTRACTS_AND_START_BY_TOKEN[integration_id]

        super().__init__(
            integration_id,
            vault_data.start,
            vault_data.chain,
            None,
            5,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        return get_effective_balance(
            user, block, self.vault_data.integration_token, self.vault_data.bridge, self.vault_data.vault_token
        )

    def get_participants(self) -> list:
        self.participants = get_vault_users(
            self.vault_data.start,
            self.vault_data.page_size,
            self.vault_data.vault_token,
            self.vault_data.chain,
        )

        return self.participants


if __name__ == "__main__":
    example_integration = LyraIntegration(IntegrationID.LYRA_SUSDE_BULL_MAINNET)
    current_block = W3_BY_CHAIN[example_integration.chain]["w3"].eth.get_block_number()

    print(example_integration.get_participants())
    print(example_integration.get_balance(example_integration.participants[0]), current_block)
