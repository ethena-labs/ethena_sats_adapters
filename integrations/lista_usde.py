from typing import Callable, Dict, List, Optional, Set

import requests

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress

lista_api_url_mainnet = "https://api.lista.org/api/moolah/ethena/position?token=usde&block={blockNumber}"

def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        response_json = response.json()
        if "data" not in response_json:
            print(f"Query failed with response: {response_json}")
            return None
        return response_json["data"]
    else:
        print(f"Query failed with status code {response.status_code}")
        return None

class ListaProtocolIntegration(
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
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
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
            if block in cached_data.keys():
                return_data[block] = cached_data[block]
                continue
            if block < self.start_block:
                return_data[block] = {}
                continue
            balances = fetch_data(lista_api_url_mainnet.format(blockNumber=block))

            if not balances:
                continue

            # Parse and save user balances
            block_balances = {}
            for entry in balances:
                try:
                    user = Web3.to_checksum_address(entry["user"])  # Ensure user address is a ChecksumAddress
                    balance =  round(float(entry["balance"]),4)  # balance is already decimal string
                    block_balances[user] = balance
                except (KeyError, ValueError) as e:
                    print(f"Error parsing balance entry: {entry}, error: {e}")
                    continue

            return_data[block] = block_balances

        return return_data


if __name__ == "__main__":
    lista_integration = ListaProtocolIntegration(
        integration_id=IntegrationID.LISTA_USDE,
        start_block=48172369,
        summary_cols=[SummaryColumn.LISTA_USDE_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=None,
    )

    print(
        lista_integration.get_block_balances(
            cached_data={}, blocks=[48172370, 50724111, 50724112]
        )
    )

    print(
        lista_integration.get_block_balances(
            cached_data={
                50724110: {
                    Web3.to_checksum_address("0x05e3a7a66945ca9af73f66660f22ffb36332fa54"): 10000,
                },
            },
            blocks=[50724110, 50724111, 50724112]
        )
    )