from requests import get
from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress

API_BASE = 'https://api.dolomite.io'

CHAIN_TO_NETWORK_MAP = {
    Chain.ARBITRUM: '42161',
    Chain.BERACHAIN: '80094',
}

CHAIN_TO_INTEGRATION_TO_MARKET_ID_MAP: dict[Chain, dict[IntegrationID, int | None]] = {
    Chain.ARBITRUM: {
        IntegrationID.DOLOMITE_USDE: 54,
        IntegrationID.DOLOMITE_SUSDE: None,
    },
    Chain.BERACHAIN: {
        IntegrationID.DOLOMITE_USDE: 14,
        IntegrationID.DOLOMITE_SUSDE: 10,
    },
}

class DolomiteIntegration(
    CachedBalancesIntegration
):
    def __init__(
            self,
            integration_id: IntegrationID,
            start_block: int,
            chain: Chain = Chain.BERACHAIN,
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
        network_id = CHAIN_TO_NETWORK_MAP[self.chain]
        market_id = CHAIN_TO_INTEGRATION_TO_MARKET_ID_MAP[self.chain][self.integration_id]

        result: Dict[int, Dict[ChecksumAddress, float]] = {}

        if market_id is None:
            return result

        for block in blocks:
            result[block] = {}
            if cached_data.__contains__(block):
                result[block] = cached_data[block]
                continue

            response = get(f'{API_BASE}/balances/{network_id}/{market_id}?blockNumber={block}&filter=supply')
            if response.status_code == 200:
                data = response.json()

                positions = data['Result']

                if positions:
                    for position in positions:
                        address = Web3.to_checksum_address(position['address'])
                        if not self.excluded_addresses or not self.excluded_addresses.__contains__(address):
                            result[block][address] = float(position['effective_balance'])
            else:
                raise Exception(f"Request failed with status code {response.status_code}: {response.text}")

        return result


if __name__ == "__main__":
    example_integration = DolomiteIntegration(
        integration_id=IntegrationID.DOLOMITE_USDE,
        start_block=849400,
        summary_cols=[SummaryColumn.DOLOMITE_BERACHAIN_USDE_PTS],
        chain=Chain.BERACHAIN,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=849500,
    )
    print(
        example_integration.get_block_balances(
            cached_data={}, blocks=[849408, 849400]
        )
    )
    # Example output:
    # {
    #   20000000: {"0x123": 100, "0x456": 200},
    #   20000001: {"0x123": 101, "0x456": 201},
    #   20000002: {"0x123": 102, "0x456": 202},
    # }

    print(
        example_integration.get_block_balances(
            cached_data={
                849408: {
                    Web3.to_checksum_address("0x09afb23aaf603868d3ee1afb13c40ff23e7c220b"): 751479.443035,
                    Web3.to_checksum_address("0x8765432187654321876543218765432187654321"): 200,
                },
                849400: {
                    Web3.to_checksum_address("0x1234567812345678123456781234567812345678"): 101,
                    Web3.to_checksum_address("0x8765432187654321876543218765432187654321"): 201,
                },
            },
            blocks=[849408],
        )
    )
    # Example output:
    # {
    #   20000002: {"0x123": 102, "0x456": 202},
    # }
