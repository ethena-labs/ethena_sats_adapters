from utils.web3_utils import call_with_retry
from constants.rho_markets import RHO_MARKETS_SCROLL_DEPLOYMENT_BLOCK, RHO_MARKETS_SCROLL_RUSDE_ADDRESS
from models.integration import Integration
from constants.summary_columns import SummaryColumn
from constants.integration_ids import IntegrationID
from constants.chains import Chain
import json
import requests
from utils.web3_utils import (
    w3_scroll,
)

with open("abi/r_token.json") as f:
    r_token_abi = json.load(f)


class RhoMarkets(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.RHO_MARKETS_USDE_LP,
            RHO_MARKETS_SCROLL_DEPLOYMENT_BLOCK,
            Chain.SCROLL,
            [SummaryColumn.RHO_MARKETS_SCROLL_SHARDS],
            20,
            1,
        )

    def get_balance(self, user: str, block: int) -> float:
        if w3_scroll.is_connected():
            print("Connected to Ethereum node")
        else:
            print("Failed to connect to Ethereum node")

        r_usde_contract = w3_scroll.eth.contract(
            address=RHO_MARKETS_SCROLL_RUSDE_ADDRESS, abi=r_token_abi
        )
        balance = call_with_retry(
            r_usde_contract.functions.balanceOf(user),
            block
        )
        exchangeRate = call_with_retry(
            r_usde_contract.functions.exchangeRateStored(),
            block
        )
        return balance * exchangeRate / (1e18 * 1e18)

    def get_participants(self) -> list:
        all_users = set()
        try:
            users = self.fetch_compound_users("rUSDe")
            for user in users:
                all_users.add(user['id'])
        except Exception as e:
            print(e)
        all_users = list(all_users)
        self.participants = all_users
        return all_users

    def fetch_compound_users(asset_symbol):
        url = "https://api.studio.thegraph.com/query/79909/rho-markets-mainnet/version/latest"
        last_id = ""
        all_accounts = []

        while True:
            query = """
            {
                accounts(first: 1000, where: { tokens_: { symbol: "%s" }, id_gt: "%s" }) {
                    id
                    tokens(where: { symbol: "%s" }) {
                        storedBorrowBalanceUSD
                        symbol
                        storedBorrowBalance
                        cTokenBalanceUSD
                        cTokenBalance
                    }
                }
            }
            """ % (asset_symbol, last_id, asset_symbol)

            response = requests.post(url, json={'query': query})

            if response.status_code == 200:
                data = response.json()
                accounts = data['data']['accounts']
                if not accounts:
                    break
                # 过滤掉0地址
                filtered_accounts = [account for account in accounts if account['id']
                                     != '0x0000000000000000000000000000000000000000']
                all_accounts.extend(filtered_accounts)
                last_id = accounts[-1]['id']
            else:
                raise Exception(f"Query failed with status code {
                                response.status_code}: {response.text}")

        return all_accounts
