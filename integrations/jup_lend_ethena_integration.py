import json
import logging
import os
import subprocess
import time
from typing import Dict, List

from dotenv import load_dotenv

from constants.jup_lend import (
    JUP_LEND_ETHENA_MARKET,
    JUP_LEND_ETHENA_START_BLOCK,
    JUP_LEND_ETHENA_VAULT_STATE_PUBKEY,
)
from constants.summary_columns import SummaryColumn
from constants.chains import Chain
from integrations.integration_ids import IntegrationID as IntID
from integrations.l2_delegation_integration import L2DelegationIntegration

load_dotenv()


class JupLendEthenaIntegration(L2DelegationIntegration):
    """
    Solana Jupiter Lend borrow vault (Ethena market): supply-side collateral
    per position NFT via ts/jup_lend_ethena_vault.ts.
    """

    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        vault_state_pubkey: str = JUP_LEND_ETHENA_VAULT_STATE_PUBKEY,
        market: str = JUP_LEND_ETHENA_MARKET,
        chain: Chain = Chain.SOLANA,
        reward_multiplier: int = 1,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=[SummaryColumn.JUP_LEND_ETHENA_PTS],
            reward_multiplier=reward_multiplier,
        )
        self.vault_state_pubkey = vault_state_pubkey
        self.market = market
        self.ts_rel_path = "ts/jup_lend_ethena_vault.ts"
        self._repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _runner_cmd(self) -> List[str]:
        script_path = os.path.join(self._repo_root, self.ts_rel_path)
        tsx_bin = os.path.join(self._repo_root, "node_modules", ".bin", "tsx")
        if os.path.isfile(tsx_bin):
            return [tsx_bin, script_path]
        return ["ts-node", script_path]

    def get_l2_block_balances(
        self, cached_data: Dict[int, Dict[str, float]], blocks: List[int]
    ) -> Dict[int, Dict[str, float]]:
        logging.info("Getting block data for Jupiter Lend (Ethena vault collateral)...")
        block_data: Dict[int, Dict[str, float]] = {}
        for block in blocks:
            block_data[block] = self.get_participants_data(block)
        return block_data

    def get_participants_data(self, block: int) -> Dict[str, float]:
        logging.info(
            f"Getting participants data for Jupiter Lend Ethena at block {block}..."
        )
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                logging.info(
                    f"Jupiter Lend Ethena snapshot at block {block} "
                    f"(attempt {retry_count + 1}/{max_retries})..."
                )
                env = os.environ.copy()
                env.setdefault("PWD", self._repo_root)
                response = subprocess.run(
                    [
                        *self._runner_cmd(),
                        self.vault_state_pubkey,
                        self.market,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                    cwd=self._repo_root,
                )
                balances = json.loads(response.stdout)
                return balances
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logging.error(
                        "Error getting Jupiter Lend Ethena participants after "
                        "%s attempts: %s",
                        max_retries,
                        e,
                    )
                    if isinstance(e, subprocess.CalledProcessError) and e.stderr:
                        logging.error("stderr: %s", e.stderr)
                    return {}
                logging.warning(
                    f"Attempt {retry_count}/{max_retries} failed, retrying..."
                )
                time.sleep(5)
        return {}


if __name__ == "__main__":
    integration = JupLendEthenaIntegration(
        integration_id=IntID.JUP_LEND_ETHENA,
        start_block=JUP_LEND_ETHENA_START_BLOCK,
        chain=Chain.SOLANA,
        reward_multiplier=1,
    )
    out = integration.get_l2_block_balances(cached_data={}, blocks=[21209856])
    print("=" * 80)
    print(out)
    print("=" * 80)
