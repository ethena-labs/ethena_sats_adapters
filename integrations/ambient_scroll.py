import requests
from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.summary_columns import SummaryColumn
from constants.ambient import AMBIENT_SCROLL_DEPLOYMENT_BLOCK, AMBIENT_SCROLL_API_URL


class Ambient(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.AMBIENT_SCROLL_LP,
            AMBIENT_SCROLL_DEPLOYMENT_BLOCK,
            Chain.SCROLL,
            [SummaryColumn.AMBIENT_SCROLL_SHARDS],
            20,  # TODO: Change 20 to the sats multiplier for the protocol that has been agreed upon
            1,
        )

    def get_balance(self, user: str, block: int) -> float:
        """
        Get the balance of a user at a given block
        """
        url = f"{AMBIENT_SCROLL_API_URL}/sats/scroll/balance"
        params = {"user": user, "block": block}
        response = requests.get(url, params=params)
        data = response.json()
        return data["data"]

    def get_participants(self) -> list:
        """
        Get all participants of the protocol, ever.
        This function should only be called once and should cache the results by setting self.participants
        """
        url = f"{AMBIENT_SCROLL_API_URL}/sats/scroll/participants"
        response = requests.get(url)
        data = response.json()
        return data["data"]


if __name__ == "__main__":
    # Simple tests for the integration
    ambient = Ambient()
    print(ambient.get_participants())
    print(ambient.get_balance(list(ambient.get_participants())[2], 7372500))
