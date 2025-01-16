import logging
import subprocess
import json

from typing import Dict, List
from dotenv import load_dotenv
from constants.summary_columns import SummaryColumn
from constants.example_integrations import (
    THALA_SUSDE_START_BLOCK,
)
from constants.thala import SUSDE_LPT_METADATA
from constants.chains import Chain
from integrations.integration_ids import IntegrationID as IntID
from integrations.l2_delegation_integration import L2DelegationIntegration

load_dotenv()

class ThalaAptosIntegration(L2DelegationIntegration):
    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        token_address: str,
        decimals: int,
        chain: Chain = Chain.APTOS,
        reward_multiplier: int = 1,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=[SummaryColumn.THALA_SHARDS],
            reward_multiplier=reward_multiplier,
        )
        self.token_address = token_address
        self.decimals = str(decimals)
        self.thala_ts_location = "ts/thala_balances.ts"

    def get_l2_block_balances(
        self, cached_data: Dict[int, Dict[str, float]], blocks: List[int]
    ) -> Dict[int, Dict[str, float]]:
        logging.info("Getting block data for Thala sUSDe LP...")
        # Ensure blocks are sorted smallest to largest
        block_data: Dict[int, Dict[str, float]] = {}
        sorted_blocks = sorted(blocks)

        # Populate block data from smallest to largest
        for block in sorted_blocks:
            # Check block_data first, then cached_data for previous block balances
            prev_block_user_balances = block_data.get(block - 1, cached_data.get(block - 1, {}))
            result = self.get_participants_data(block, prev_block_user_balances)

            # Store the balances
            block_data[block] = result['balances']

        return block_data

    def get_participants_data(self, block, prev_block_user_balances=None):
        print("Getting participants data for block", block)
        try:
            response = subprocess.run(
                [
                    "ts-node",
                    self.thala_ts_location,
                    SUSDE_LPT_METADATA,
                    str(self.decimals),
                    str(block),
                    json.dumps(prev_block_user_balances or {}),
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
                return result
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
    example_integration = ThalaAptosIntegration(
        integration_id=IntID.THALA_SUSDE_LP,
        start_block=THALA_SUSDE_START_BLOCK,
        token_address=SUSDE_LPT_METADATA,
        decimals=8,
        chain=Chain.APTOS,
        reward_multiplier=5,
    )

    example_integration_output = example_integration.get_l2_block_balances(
        cached_data={}, blocks=list(range(THALA_SUSDE_START_BLOCK, THALA_SUSDE_START_BLOCK + 300))
    )

    print("=" * 120)
    print("Run without cached data", example_integration_output)
    print("=" * 120, "\n" * 5)