from typing import Dict, List, Optional, Set
import requests
from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID


class BlackholeIntegration(CachedBalancesIntegration):
    """Integration for tracking Blackhole LP positions (sUSDe)"""

    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain = Chain.AVALANCHE,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 30,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block: Optional[int] = None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func: Optional[callable] = None,
        ticker: str = "sUSDe",
        token_address: str = "0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2",
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
        # Base URL without query params
        self.api_url = (
            "https://api.blackhole.xyz/"
            "totalPoolBalances"
        )
        self.ticker = ticker
        self.token_address = token_address

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Fetch balances for sUSDe on Blackhole by block number, with isNext pagination."""
        result = {}

        for block in blocks:
            if block in cached_data:
                print(f"[INFO] Using cached data for block {block}")
                result[block] = cached_data[block]
                continue

            block_data: Dict[ChecksumAddress, float] = {}
            page_number = 1

            try:
                while True:
                    print(f"[INFO] Fetching block={block}, page={page_number}")

                    response = requests.get(
                        self.api_url,
                        params={
                            "ticker": self.ticker,
                            "tokenAddress": self.token_address,
                            "blockNumber": block,
                            "pageNumber": page_number,
                        },
                        timeout=10,
                    )
                    print(f"[INFO] Response status={response.status_code}")

                    try:
                        data = response.json()
                    except Exception as e:
                        print(
                            f"[DEBUG] Failed to decode JSON: {e}, "
                            f"text={response.text[:200]}"
                        )
                        break

                    print(f"[INFO] Keys in response: {list(data.keys())}")

                    balances = {}
                    if "data" in data and isinstance(data["data"], dict):
                        balances = data["data"].get("balances", {})
                        print(f"[INFO] Using 'data.balances', count={len(balances)}")
                        is_next = data["data"].get("isNext", False)
                    elif "aggregatedBalances" in data:
                        balances = data["aggregatedBalances"]
                        print(
                            f"[INFO] Using 'aggregatedBalances', count={len(balances)}"
                        )
                        is_next = data.get("isNext", False)
                    else:
                        print("[INFO] No balances field found")
                        break

                    if not balances:
                        print(
                            f"[INFO] No balances found, breaking loop at page {page_number}"
                        )
                        break

                    for addr, bal in balances.items():
                        print(f"[INFO] addr={addr}, bal={bal}")
                        checksum_addr = Web3.to_checksum_address(addr)
                        value = float(bal)
                        if value > 0:
                            block_data[checksum_addr] = block_data.get(
                                checksum_addr, 0.0
                            ) + value

                    if is_next:
                        page_number += 1
                        print(f"[INFO] isNext=True → Moving to next page={page_number}")
                    else:
                        print("[INFO] isNext=False → Stopping pagination")
                        break

            except Exception as e:
                print(
                    f"Error fetching data for block {block}, page {page_number}: {str(e)}"
                )
                break

            result[block] = block_data

        return result


if __name__ == "__main__":
    # Simple test
    integration = BlackholeIntegration(
        integration_id=IntegrationID.BLACKHOLE_SUSDE_POOL,
        start_block=69219496,
        chain=Chain.AVALANCHE,
        summary_cols=[SummaryColumn.BLACKHOLE_POOL_PTS],
        reward_multiplier=1,
    )

    result = integration.get_block_balances(cached_data={}, blocks=[69219496])
    print("Block balances:", result)
