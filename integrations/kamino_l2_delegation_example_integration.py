import logging
import os
import subprocess
import json
import time

from typing import Dict, List
from dotenv import load_dotenv
from constants.summary_columns import SummaryColumn
from constants.example_integrations import (
    KAMINO_SUSDE_COLLATERAL_START_BLOCK_EXAMPLE,
)
from constants.chains import Chain
from integrations.integration_ids import IntegrationID as IntID
from integrations.l2_delegation_integration import L2DelegationIntegration

load_dotenv()


class KaminoL2DelegationExampleIntegration(L2DelegationIntegration):
    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        token_address: str,
        market_address: str,
        decimals: int,
        chain: Chain = Chain.SOLANA,
        reward_multiplier: int = 1,
    ):

        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=[SummaryColumn.KAMINO_DELEGATED_PTS_EXAMPLE],
            reward_multiplier=reward_multiplier,
        )
        self.token_address = token_address
        self.market_address = market_address
        self.decimals = str(decimals)
        self.kamino_ts_location = "ts/kamino_collat.ts"

    def get_l2_block_balances(
        self, cached_data: Dict[int, Dict[str, float]], blocks: List[int]
    ) -> Dict[int, Dict[str, float]]:
        logging.info("Getting block data for Kamino l2 delegation example...")
        block_data: Dict[int, Dict[str, float]] = {}
        for block in blocks:
            block_data[block] = self.get_participants_data(block)
        return block_data

    def get_participants_data(self, block: int) -> Dict[str, float]:
        logging.info(
            f"Getting participants data for Kamino l2 delegation example at block {block}..."
        )
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                logging.info(
                    f"Getting participants data for Kamino l2 delegation example at block {block}... (Attempt {retry_count + 1}/{max_retries})"
                )
                response = subprocess.run(
                    [
                        "ts-node",
                        os.path.join(
                            os.path.dirname(__file__), "..", self.kamino_ts_location
                        ),
                        self.market_address,
                        self.token_address,
                        self.decimals,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=os.environ.copy(),
                )
                balances = json.loads(response.stdout)
                return balances
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    err_msg = f"Error getting participants data for Kamino l2 delegation example after {max_retries} attempts: {e}"
                    logging.error(err_msg)
                    return {}
                else:
                    logging.warning(
                        f"Attempt {retry_count}/{max_retries} failed, retrying..."
                    )
                    time.sleep(5)  # Add a small delay between retries
        return {}


if __name__ == "__main__":
    example_integration = KaminoL2DelegationExampleIntegration(
        integration_id=IntID.KAMINO_SUSDE_COLLATERAL_EXAMPLE,
        start_block=KAMINO_SUSDE_COLLATERAL_START_BLOCK_EXAMPLE,
        market_address="BJnbcRHqvppTyGesLzWASGKnmnF1wq9jZu6ExrjT7wvF",
        token_address="EwBTjwCXJ3TsKP8dNTYnzRmBWRd6h48FdLFSAGJ3sCtx",
        decimals=9,
        chain=Chain.SOLANA,
        reward_multiplier=5,
    )

    example_integration_output = example_integration.get_l2_block_balances(
        cached_data={}, blocks=[21209856, 21217056]
    )

    print("=" * 120)
    print("Run without cached data", example_integration_output)
    print("=" * 120, "\n" * 5)
