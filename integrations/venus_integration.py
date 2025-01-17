import json
import os
from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress
import requests

from utils.web3_utils import (
    W3_BY_CHAIN,
)

with open("abi/venus_vtoken.json") as f:
    venus_vtoken_abi = json.load(f)


venus_isolated_pools_subgraph_url_mainnet = f"https://gateway.thegraph.com/api/{os.getenv('VENUS_SUBGRAPH_API_KEY')}/subgraphs/id/Htf6Hh1qgkvxQxqbcv4Jp5AatsaiY5dNLVcySkpCaxQ8"

supplier_balance_query = """{{
  marketPositions(where: {{market: "{marketAddress}", vTokenBalanceMantissa_gt: 0}}, block :{{number: {blockNumber}}}) {{
    account {{
      id
    }}
    vTokenBalanceMantissa
  }}
}}
"""

# Helper for making graphql queries
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

vsUSDE = "0x0792b9c60C728C1D2Fd6665b3D7A08762a9b28e0"
sUSDE_DECIMALS = 18

class VenusProtocolIntegration(
    CachedBalancesIntegration
):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = {
            Web3.to_checksum_address(vsUSDE)},
        end_block: Optional[int] = None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func: Optional[Callable[[int, str], int]] = None,
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            summary_cols,
            reward_multiplier,
            balance_multiplier,
            excluded_addresses,
            end_block,
            ethereal_multiplier,
            ethereal_multiplier_func,
        )

        self.vsUSDE_contract = W3_BY_CHAIN[self.chain]["w3"].eth.contract(
            address=Web3.to_checksum_address(vsUSDE),
            abi=venus_vtoken_abi
        )

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Get user balances for specified blocks, using cached data when available.

        Args:
            cached_data (Dict[int, Dict[ChecksumAddress, float]]): Dictionary mapping block numbers
                to user balances at that block. Used to avoid recomputing known balances.
                The inner dictionary maps user addresses to their token balance.
            blocks (List[int]): List of block numbers to get balances for.

        Returns:
            Dict[int, Dict[ChecksumAddress, float]]: Dictionary mapping block numbers to user balances,
                where each inner dictionary maps user addresses to their token balance
                at that block.
        """
        return_data = {}

        for block in blocks:
            exchange_rate = self.vsUSDE_contract.functions.exchangeRateCurrent().call(block_identifier=block)
            if block in cached_data.keys():
                return_data[block] = cached_data[block]
                continue

            balances = fetch_data(venus_isolated_pools_subgraph_url_mainnet, supplier_balance_query.format(marketAddress=vsUSDE, blockNumber=block))

            if balances: 
                if len(balances['marketPositions']) > 0:
                    return_data[block] = {}

                for balance in balances['marketPositions']:
                    return_data[block][balance['account']['id']] = (exchange_rate * int(balance['vTokenBalanceMantissa'])) / (10 ** (18 + sUSDE_DECIMALS))

        return return_data


if __name__ == "__main__":

    venus_integration = VenusProtocolIntegration(
        integration_id=IntegrationID.VENUS_SUSDE,
        start_block=21441891,
        summary_cols=[SummaryColumn.VENUS_SUSDE_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=40000000,
    )
    
    print(
        venus_integration.get_block_balances(
            cached_data={}, blocks=[21524870, 21524871, 21524872]
        )
    )

    print(
        venus_integration.get_block_balances(
            cached_data={
                21524871: {
                    Web3.to_checksum_address("0x3e8734Ec146C981E3eD1f6b582D447DDE701d90c"): 10000,
                },
            },
            blocks=[21524870, 21524871, 21524872]
        )
    )
