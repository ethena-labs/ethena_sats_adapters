import json
import logging
from typing import Dict, List, Optional
from eth_typing import ChecksumAddress
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from constants.wildcat import WILDCAT_MARKET_ADDRESS, WILDCAT_SUBGRAPH_URL
import requests
from web3 import Web3

# query to fetch active lenders and their scaled balances at a block
ACTIVE_LENDERS_QUERY = """{{
  market(id: "{market}", block: {{number: {block}}}) {{
    scaleFactor
    decimals
    lenders(first: 1000) {{
      address
      scaledBalance
    }}
  }}
}}
"""


def fetch_data(url, query):
    response = requests.post(url, json={"query": query})
    if response.status_code == 200:
        response_json = response.json()
        if "data" not in response_json:
            logging.error(f"Query failed with response: {response_json}")
            return None
        return response_json["data"]
    else:
        logging.error(f"Query failed with status code {response.status_code}")
        return None


class WildcatIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            summary_cols,
            reward_multiplier,
        )

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block data for Wildcat lenders")
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to Wildcat get_block_balances")
            return new_block_data

        sorted_blocks = sorted(blocks)
        cache_copy = {**cached_data}

        for block in sorted_blocks:
            if block in cache_copy:
                new_block_data[block] = cache_copy[block]
                continue

            query = ACTIVE_LENDERS_QUERY.format(market=WILDCAT_MARKET_ADDRESS.lower(), block=block)
            data = fetch_data(WILDCAT_SUBGRAPH_URL, query)
            if data is None or data.get("market") is None:
                logging.warning(f"No market data returned for block {block}")
                new_block_data[block] = {}
                cache_copy[block] = {}
                continue

            market_data = data["market"]
            # grab scaleFactor from subgraph (ray-scaled integer)
            scale_factor = int(market_data.get("scaleFactor") or 10**27)
            decimals = int(market_data.get("decimals") or 18)

            lenders = market_data["lenders"]
            balances = {}
            for lender in lenders:
                addr = Web3.to_checksum_address(lender["address"])
                scaled = int(lender.get("scaledBalance", 0))
                # normalized = rayMul(scaled, scaleFactor) per Wildcat SDK
                from utils.wildcat import rayMul
                normalized = rayMul(scaled, scale_factor)
                # Convert to float of market token units using the market token decimals from subgraph
                balances[addr] = float(normalized) / (10 ** decimals)

            new_block_data[block] = balances
            cache_copy[block] = balances

        return new_block_data


if __name__ == "__main__":
    """
    Test script for the Wildcat integration.
    This is for development/testing only and not used when the integration is run as part of the Ethena system.
    """

    # Create example integration
    integration = WildcatIntegration(
        integration_id=IntegrationID.WILDCAT_MARKET_DEBT,
        start_block=23196291,
        summary_cols=[SummaryColumn.WILDCAT_MARKET_DEBT_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        # exclude zero address by default
        # (update with real excluded addresses if needed)
        # type: ignore[arg-type]
        # Note: Integration constructor accepts excluded_addresses in CachedBalancesIntegration
    )

    print("Testing Wildcat Integration")
    print("=" * 60)

    # Test without cached data
    test_blocks = [23196290, 23196291]
    print("Blocks to fetch (no cache):", test_blocks)
    without_cached_data_output = integration.get_block_balances(cached_data={}, blocks=test_blocks)
    print("Without cached data:")
    print(json.dumps(without_cached_data_output, indent=2))
    print()

    # Test with cached data (simulate previously computed block)
    cached_data = {
        23196290: {
            Web3.to_checksum_address("0x1234567890123456789012345678901234567890"): 100.0,
        }
    }

    with_cached_data_output = integration.get_block_balances(
        cached_data=cached_data, blocks=[23196291]
    )
    print("With cached data (only fetching missing blocks):")
    print(json.dumps(with_cached_data_output, indent=2))
    print()

    print("Wildcat Integration test completed!")
