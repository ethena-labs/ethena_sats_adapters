import requests
from constants.chains import Chain
from models.integration import Integration
from integrations.integration_ids import IntegrationID

from constants.beefy import BEEFY_LRT_API_URL

CHAIN_TO_API_URL_PREFIX = {
    [Chain.ARBITRUM]: f"{BEEFY_LRT_API_URL}/api/v2/partner/ethena/arbitrum",
    [Chain.FRAXTAL]: f"{BEEFY_LRT_API_URL}/api/v2/partner/ethena/fraxtal",
    [Chain.MANTLE]: f"{BEEFY_LRT_API_URL}/api/v2/partner/ethena/mantle",
    [Chain.OPTIMISM]: f"{BEEFY_LRT_API_URL}/api/v2/partner/ethena/optimism",
}


class BeefyIntegration(Integration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain,
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            None,
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        """
        Get the balance of a user at a given block
        """

        base_url = CHAIN_TO_API_URL_PREFIX[self.chain]
        url = f"{base_url}/user/{user}/balance/{block}"
        response = requests.get(url)
        data = response.json()

        return float(data["effective_balance"])

    def get_participants(self) -> list:
        """
        Get all participants of the protocol, ever.
        This function should only be called once and should cache the results by setting self.participants
        """
        base_url = CHAIN_TO_API_URL_PREFIX[self.chain]
        url = f"{base_url}/users"
        response = requests.get(url)
        data = response.json()

        self.participants = data

        return data
