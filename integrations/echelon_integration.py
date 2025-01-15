import logging
import subprocess
import json

from typing import Dict, List
from dotenv import load_dotenv
from constants.summary_columns import SummaryColumn
from constants.example_integrations import (
    ECHELON_SUSDE_COLLATERAL_START_BLOCK,
)
from constants.echelon import LENDING_CONTRACT_ADDRESS, SUSDE_MARKET_ADDRESS, SUSDE_TOKEN_ADDRESS
from constants.chains import Chain
from integrations.integration_ids import IntegrationID as IntID
from integrations.l2_delegation_integration import L2DelegationIntegration

load_dotenv()

class EchelonAptosIntegration(L2DelegationIntegration):
    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        token_address: str,
        market_address: str,
        decimals: int,
        chain: Chain = Chain.APTOS,
        reward_multiplier: int = 1,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=[SummaryColumn.ECHELON_SHARDS],
            reward_multiplier=reward_multiplier,
        )
        self.token_address = token_address
        self.market_address = market_address
        self.decimals = str(decimals)
        self.echelon_ts_location = "ts/echelon_balances.ts"
        self.exchange_rate_cache: float = 0

    def get_l2_block_balances(
        self, cached_data: Dict[int, Dict[str, float]], blocks: List[int]
    ) -> Dict[int, Dict[str, float]]:
        logging.info("Getting block data for Echelon sUSDe Collateral...")
        # Ensure blocks are sorted smallest to largest
        block_data: Dict[int, Dict[str, float]] = {}
        sorted_blocks = sorted(blocks)

        # Populate block data from smallest to largest
        for block in sorted_blocks:
            # Check block_data first, then cached_data for previous block balances
            prev_block_user_balances = block_data.get(block - 1, cached_data.get(block - 1, {}))
            result = self.get_participants_data(block, prev_block_user_balances)

            # Store the balances and cache the exchange rate
            block_data[block] = result['balances']
            self.exchange_rate_cache = result['exchange_rate']

        return block_data

    def get_participants_data(self, block, prev_block_user_balances=None):
        print("Getting participants data for block", block)
        try:
            response = subprocess.run(
                [
                    "ts-node",
                    self.echelon_ts_location,
                    LENDING_CONTRACT_ADDRESS,
                    self.market_address,
                    str(self.decimals),
                    str(block),
                    json.dumps(prev_block_user_balances or {}),
                    str(self.exchange_rate_cache)
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Debug output
            print("TypeScript stdout:", response.stdout)
            print("TypeScript stderr:", response.stderr)
            
            try:
                result = json.loads(response.stdout)
                return result  # Now returns dict with both balances and exchange rate
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Raw output: {response.stdout}")
                raise
                
        except subprocess.CalledProcessError as e:
            print(f"Process error: {e}")
            print(f"stderr: {e.stderr}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


if __name__ == "__main__":
    example_integration = EchelonAptosIntegration(
        integration_id=IntID.ECHELON_SUSDE_COLLATERAL,
        start_block=ECHELON_SUSDE_COLLATERAL_START_BLOCK,
        market_address=SUSDE_MARKET_ADDRESS,
        token_address=SUSDE_TOKEN_ADDRESS,
        decimals=6,
        chain=Chain.APTOS,
        reward_multiplier=5,
    )

    example_integration_output = example_integration.get_l2_block_balances(
        cached_data={}, blocks=list(range(ECHELON_SUSDE_COLLATERAL_START_BLOCK, ECHELON_SUSDE_COLLATERAL_START_BLOCK + 300))
    )

    print("=" * 120)
    print("Run without cached data", example_integration_output)
    print("=" * 120, "\n" * 5)