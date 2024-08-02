import json
import requests
from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.summary_columns import SummaryColumn
from utils.web3_utils import w3_arb, fetch_events_logs_with_retry, call_with_retry

from constants.gmx import GMX_SYNTHETICS_READER_CONTRACT_ADDRESS, GMX_WSTETH_USDE_MARKET_ADDRESS, GMX_DATA_STORE_CONTRACT_ADDRESS, GMX_USDE_USDC_MARKET_ADDRESS, GMX_MAX_PNL_FACTOR_FOR_TRADERS_KEY, GMX_PRICES_ENDPOINT

with open("abi/gmx_gm_token.json") as f:
    gmx_gm_token_abi = json.load(f)

with open("abi/gmx_synthetics_reader_contract.json") as f:
    gmx_synthetics_reader_contract_abi = json.load(f)

gmx_usde_usdc_market_contract = w3_arb.eth.contract(
    address=GMX_USDE_USDC_MARKET_ADDRESS, abi=gmx_gm_token_abi
)

gmx_wsteth_usde_market_contract = w3_arb.eth.contract(
    address=GMX_WSTETH_USDE_MARKET_ADDRESS, abi=gmx_gm_token_abi
)

gmx_synthetics_reader_contract = w3_arb.eth.contract(
    address=GMX_SYNTHETICS_READER_CONTRACT_ADDRESS, abi=gmx_synthetics_reader_contract_abi
)

def makePriceTuple(prices, token):
    return (
        int(prices[token]['minPrice']),
        int(prices[token]['maxPrice']),
    )

def getContract(contract_address):
    if contract_address == GMX_USDE_USDC_MARKET_ADDRESS:
        return gmx_usde_usdc_market_contract
    elif contract_address == GMX_WSTETH_USDE_MARKET_ADDRESS:
        return gmx_wsteth_usde_market_contract
    else:
        return None

class GMXLPIntegration(Integration):
    prices = None
    market_address = None
    market_contract = None
    index_token_address = None
    long_token_address = None
    short_token_address = None

    def __init__(
            self,
            integration_id: IntegrationID,
            start_block: int,
            market_address: str,
            index_token_address: str,
            long_token_address: str,
            short_token_address: str,
        ):
        super().__init__(
            integration_id,
            start_block,
            Chain.ARBITRUM,
            [SummaryColumn.GMX_ARBITRUM_SHARDS],
            20,
            1,
            None,
            None,
        )
        self.market_address = market_address
        self.market_contract = getContract(market_address)
        self.index_token_address = index_token_address
        self.long_token_address = long_token_address
        self.short_token_address = short_token_address

    def get_balance(self, user: str, block: int) -> float:
        marketPrices = self.fetchTokenPrices()

        marketParams = [
            self.market_address,
            self.index_token_address,
            self.long_token_address,
            self.short_token_address,
        ]

        marketTokenPrice = call_with_retry(
            gmx_synthetics_reader_contract.functions.getMarketTokenPrice(
                GMX_DATA_STORE_CONTRACT_ADDRESS,
                marketParams,
                makePriceTuple(marketPrices, self.index_token_address),
                makePriceTuple(marketPrices, self.long_token_address),
                makePriceTuple(marketPrices, self.short_token_address),
                GMX_MAX_PNL_FACTOR_FOR_TRADERS_KEY,
                False,
            )
        )

        user_token_balance = call_with_retry(
            self.market_contract.functions.balanceOf(user),
            block,
        )

        gm_token_price = marketTokenPrice[0]
        oracle_price_decimals = 1e30

        return gm_token_price * user_token_balance / oracle_price_decimals

    def get_participants(self) -> list:
        if self.participants is not None:
            return self.participants

        page_size = 1900
        start_block = self.start_block
        target_block = w3_arb.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"GMX V2 Arbitrum USDE/USDC LP users from {start_block} to {to_block}",
                self.market_contract.events.Transfer(),
                start_block,
                to_block,
            )
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
            start_block += page_size

        all_users = list(all_users)
        self.participants = all_users
        return all_users

    def fetchTokenPrices(self):
        if (self.prices):
            return self.prices

        response = requests.get(GMX_PRICES_ENDPOINT)

        if response.status_code == 200:
            pricesCollection = response.json()
            pricesDict = { item['tokenAddress']: item for item in pricesCollection }
            self.prices = pricesDict
            return self.prices

        print(f"GMX: failed to fetch token prices with status code {response.status_code}")

        return None