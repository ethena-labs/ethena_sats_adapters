from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from constants.velodrome import VELODROME_INK_START_BLOCK, SUSDE_INK_TOKEN
from utils.velodrome import fetch_ink_balance, fetch_ink_participants


class VelodromeIntegration(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.VELODROME_INK_SUSDE,
            VELODROME_INK_START_BLOCK,
            Chain.INK,
            None,
            20,
            1,
            None,
            None,
        )

    def get_ink_balance(self, user: str, block: int) -> float:
        return fetch_ink_balance(user, block, SUSDE_INK_TOKEN)

    def get_ink_participants(self, blocks: list[int] | None = None) -> set[str]:
        return fetch_ink_participants(SUSDE_INK_TOKEN)


if __name__ == "__main__":
    velodrome_integration = VelodromeIntegration()