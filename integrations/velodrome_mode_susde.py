from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from constants.velodrome import VELODROME_MODE_START_BLOCK, SUSDE_MODE_TOKEN
from utils.velodrome import fetch_balance, fetch_participants


class VelodromeIntegration(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.VELODROME_MODE_SUSDE,
            VELODROME_MODE_START_BLOCK,
            Chain.MODE,
            None,
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        return fetch_balance(user, block, SUSDE_MODE_TOKEN)

    def get_participants(self, blocks: list[int] | None = None) -> set[str]:
        return fetch_participants(SUSDE_MODE_TOKEN)


if __name__ == "__main__":
    velodrome_integration = VelodromeIntegration()
