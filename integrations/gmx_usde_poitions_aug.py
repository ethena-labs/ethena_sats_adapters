import requests
from integrations.integration_ids import IntegrationID
from constants.chains import Chain

from constants.gmx import (
    GMX_DATA_STORE_CONTRACT_ADDRESS,
    GMX_WSTETH_USDE_MARKET_BLOCK,
    GMX_SUBSQUID_ENDPOINT,
    USDE_TOKEN_ADDRESS,
)
from utils.gmx import gmx_synthetics_reader_contract
from constants.summary_columns import SummaryColumn
from integrations.integration import Integration
from utils.web3_utils import call_with_retry


def fetch_data(url, query):
    response = requests.post(url, json={"query": query})
    if response.status_code == 200:
        response_json = response.json()
        if "data" not in response_json:
            print(f"Query failed with response: {response_json}")
            return None
        return response_json["data"]
    else:
        print(f"Query failed with status code {response.status_code}")
        return None


class GMXPositionsIntegration(Integration):
    def __init__(
        self,
    ):
        super().__init__(
            IntegrationID.GMX_USDE_POSITIONS,
            GMX_WSTETH_USDE_MARKET_BLOCK,
            Chain.ARBITRUM,
            [SummaryColumn.GMX_ARBITRUM_SHARDS],
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        accountPositions = call_with_retry(
            gmx_synthetics_reader_contract.functions.getAccountPositions(
                GMX_DATA_STORE_CONTRACT_ADDRESS,
                user,
                0,
                1000,
            ),
            block,
        )

        total_collateral_amount = 0

        for position in accountPositions:
            collateral_token = position[0][2]
            collateral_amount = position[1][2]

            if collateral_token == USDE_TOKEN_ADDRESS:
                total_collateral_amount += collateral_amount

        return total_collateral_amount

    def get_participants(self) -> list:
        if self.participants is not None:
            return self.participants

        participants_query = """{{
            positions(
                where: {{
                collateralToken_eq: "{collateralTokenw}",
              }}
            ) {{
                account
              }}
        }}"""

        participants = fetch_data(
            url=GMX_SUBSQUID_ENDPOINT,
            query=participants_query.format(
                collateralTokenw=USDE_TOKEN_ADDRESS,
            ),
        )

        accounts = [position["account"] for position in participants["positions"]]

        return list(set(accounts))


if __name__ == "__main__":
    gmx_integration = GMXPositionsIntegration()
    # print(gmx_integration.get_participants())
    print(
        gmx_integration.get_balance(
            "0xDb59AB7d951f3D9F1d2E764c3A6F7507E11a4e4e", 238320844
        )
    )
