from constants.chains import Chain
from utils.web3_utils import w3
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
import requests

ZEOLEND_API_URL = "https://api.zerolend.xyz"


class ZerolendIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        reward_multiplier: int,
        token: str,
    ):
        super().__init__(
            integration_id,
            20000000,  # not used
            Chain.ETHEREUM,
            None,
            reward_multiplier,
            1,
            None,
            None,
        )

        self.token = token
    def get_balance(self, user: str, block: int) -> float:
        try:
            url = f"{ZEOLEND_API_URL}/ethena"  # TODO: add api url
            params = {"token": self.token, "address": str(user), "blockNo": str(block)}
            response = requests.get(url, params=params)  # type: ignore
            print(response.json())
            data = response.json()
            asset_balance = data["data"]
            return asset_balance
        except Exception as ex:
            print("Error getting balance for user %s: %s", user, ex)
            return 0

    def get_participants(self, blocks: list[int] | None) -> set[str]:
        """
        Get all participants of the protocol, ever.
        This function should only be called once and should cache the results by setting self.participants
        """
        url = f"{ZEOLEND_API_URL}/ethena/participants"
        params = {"token": self.token}
        response = requests.get(url, params=params)
        data = response.json()
        return data["data"]


if __name__ == "__main__":
    zerolend = ZerolendIntegration(IntegrationID.ZEROLEND_SUSDE, 5, "susde")
    # zerolend = ZerolendIntegration(IntegrationID.ZEROLEND_USDE, 20, "usde")
    participants = zerolend.get_participants(None)
    print("participants", participants)
    currentBlock = w3.eth.get_block_number()
    if len(participants) > 0:
        print(
            zerolend.get_balance(
                list(participants)[len(participants) - 1], currentBlock
            )
        )
