import json
import subprocess
import os
import logging

from typing import Dict, List, Optional
from constants.integration_token import Token
from constants.stonfi import STONFI_USDE_START_BLOCK
from integrations.l2_delegation_integration import L2DelegationIntegration
from utils.web3_utils import get_block_date
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.integration_ids import IntegrationID
from utils.request_utils import requests_retry_session
from utils.slack import slack_message

STONFI_ENDPOINT = "https://api.ston.fi"

STONFI_LP_TOKEN_DECIMALS = 9

TOKEN_SYMBOL_POOLS_MAP = {
    Token.USDE: [
        "EQBSUY4UWGJFAps0KwHY4tpOGqzU41DZhyrT8OuyAWWtnezy", # https://app.ston.fi/pools/EQBSUY4UWGJFAps0KwHY4tpOGqzU41DZhyrT8OuyAWWtnezy
    ],
}

class StonFiIntegration(L2DelegationIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        summary_cols: Optional[List[SummaryColumn]] = None,
        chain: Chain = Chain.TON,
        reward_multiplier: int = 1,
        end_block: Optional[int] = None,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols if summary_cols else [SummaryColumn.STONFI_USDE_PTS],
            reward_multiplier=reward_multiplier,
            end_block=end_block,
        )
        self.is_farmix_position_ts_location = "ts/farmix_position_check.ts"

    def get_token_symbol(self):
        return self.integration_id.get_token()

    def get_l2_block_balances(
        self,
        cached_data: Dict[int, Dict[str, float]],
        blocks: List[int]
    ) -> Dict[int, Dict[str, float]]:
        logging.info(
            f"Getting block data for STON.fi L2 delegation and blocks {blocks}..."
        )

        data_per_block: Dict[int, Dict[str, float]] = {}

        for target_block in blocks:
            if self.start_block > target_block or (
                self.end_block and target_block > self.end_block
            ):
                data_per_block[target_block] = {}
                continue
            data_per_block[target_block] = self.get_participants_data(target_block)

        return data_per_block

    def get_participants_data(self, block: int) -> Dict[str, float]:
        # block timestamp format "2025-01-16T01:00:00"
        target_date = get_block_date(block, self.chain, adjustment=3600, fmt="%Y-%m-%dT%H:%M:%S")

        logging.info(
            f"Fetching participants data for STON.fi L2 delegation at block {block} timestamp {target_date}..."
        )

        pools_list = TOKEN_SYMBOL_POOLS_MAP[self.get_token_symbol()]
        lp_token_decimals_base = 10 ** STONFI_LP_TOKEN_DECIMALS

        block_data: Dict[str, float] = {}
        try:
            for pool_address in pools_list:
                # example: https://api.ston.fi/v1/snapshots/liquidity_providers?timestamp=2025-05-09T10:00:00&pool_address=EQBSUY4UWGJFAps0KwHY4tpOGqzU41DZhyrT8OuyAWWtnezy
                res = requests_retry_session().get(
                    STONFI_ENDPOINT + "/v1/snapshots/liquidity_providers",
                    params={
                        "pool_address": pool_address,
                        "timestamp": target_date
                    },
                    timeout=60,
                )
                payload = res.json()

                snapshot = payload["snapshot"]

                if len(snapshot) != 1:
                    raise Exception("Invalid liquidity providers snapshot data")

                pool_snapshot = snapshot[0]
                lp_price_usd = float(pool_snapshot["lp_price_usd"])

                for position in pool_snapshot["positions"]:
                    wallet_address = position["wallet_address"]
                    lp_token_amount = int(position["lp_amount"]) + int(position["staked_lp_amount"])
                    position_value_usd = lp_token_amount * lp_price_usd / lp_token_decimals_base
                    is_contract_farmix_position = self.get_contract_is_farmix_position(wallet_address)

                    real_wallet_addr = wallet_address
                    if (
                            'is_position' in is_contract_farmix_position
                            and is_contract_farmix_position['is_position']
                            and 'owner_addr' in is_contract_farmix_position
                    ):
                        real_wallet_addr = is_contract_farmix_position['owner_addr']
                        logging.info(f"farmix position detected stonfi lp provider {wallet_address} is farmix position with owner {real_wallet_addr}")

                    block_data[real_wallet_addr] = block_data.get(wallet_address, 0) + position_value_usd

        except Exception as e:
            # pylint: disable=line-too-long
            err_msg = f"Error getting participants data for STON.fi L2 delegation at block {block}: {e}"
            logging.error(err_msg)
            slack_message(err_msg)

        return block_data

    def get_contract_is_farmix_position(self, addr: str):
        logging.debug(
            f"Getting constract is farmix position for addr ${addr}..."
        )
        max_retries = 1
        retry_count = 0

        while retry_count < max_retries:
            retry_count += 1
            try:
                response = subprocess.run(
                    [
                        "tsx",
                        os.path.join(
                            os.path.dirname(
                                __file__), "..", self.is_farmix_position_ts_location
                        ),
                        addr,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=os.environ.copy(),
                )
                result = json.loads(response.stdout)
                if hasattr(result, 'err'):
                    logging.error(result.err)
                else:
                    return result
            except Exception as e:
                logging.error(e)

        return {}


if __name__ == "__main__":
    stonfi_integration = StonFiIntegration(
        integration_id=IntegrationID.STONFI_USDE,
        start_block=STONFI_USDE_START_BLOCK,
        summary_cols=[
            SummaryColumn.STONFI_USDE_PTS,
        ],
        chain=Chain.TON,
        reward_multiplier=1,
    )

    stonfi_integration_output = stonfi_integration.get_l2_block_balances(
        cached_data={},
        blocks=[22445190, 22445191, 22445550, 22497283], # https://etherscan.io/blocks?p=1
    )

    print("=" * 120)
    print("Run without cached data", json.dumps(stonfi_integration_output, indent=2))
    print("=" * 120, "\n" * 5)
