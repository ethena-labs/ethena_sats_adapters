import requests
from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from constants.summary_columns import SummaryColumn
from constants.ambient import AMBIENT_SWELL_DEPLOYMENT_BLOCK, AMBIENT_API_URL


class Ambient(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.AMBIENT_SWELL_LP,
            AMBIENT_SWELL_DEPLOYMENT_BLOCK,
            Chain.SWELL,
            [SummaryColumn.AMBIENT_SWELL_SHARDS],
            20,  # TODO: Change 20 to the sats multiplier for the protocol that has been agreed upon
            1,
        )

    def get_balance(self, user: str, block: int) -> float:
        """
        Get the balance of a user at a given block
        """
        url = f"{AMBIENT_API_URL}/sats/swell/balance"
        params = {"user": str(user), "block": str(block)}
        response = requests.get(url, params=params)  # type: ignore
        data = response.json()
        return data["data"]

    def get_participants(self, blocks: list[int] | None) -> set[str]:
        """
        Get all participants of the protocol, ever.
        This function should only be called once and should cache the results by setting self.participants
        """
        url = f"{AMBIENT_API_URL}/sats/swell/participants"
        response = requests.get(url)
        data = response.json()
        return data["data"]


if __name__ == "__main__":
    # Simple tests for the integration
    ambient = Ambient()
    print(ambient.get_participants(None))
    print(ambient.get_balance(
        list(ambient.get_participants(None))[2], 978000))
