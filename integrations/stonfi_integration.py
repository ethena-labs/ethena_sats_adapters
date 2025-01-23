import json
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

TOKEN_SYMBOL_ADDRESS_MAP = {
    Token.USDE: "EQA2kCVNwVsil2EM2mB0SkXytxCqQjS4mttjDpnXmwG9T6bO",  # FIXME: replace with real USDe address
}

TOKEN_DECIMALS_MAP = {
    Token.USDE: 9,  # FIXME: replace with real USDe decimals
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
        target_date = get_block_date(block, Chain.ETHEREUM, adjustment=3600, fmt="%Y-%m-%dT%H:%M:%S")

        logging.info(
            f"Fetching participants data for STON.fi L2 delegation at block {block} timestamp {target_date}..."
        )

        token_address = TOKEN_SYMBOL_ADDRESS_MAP[self.get_token_symbol()]
        token_decimals = TOKEN_DECIMALS_MAP[self.get_token_symbol()]
        token_decimals_base = 10 ** token_decimals

        block_data: Dict[str, float] = {}
        try:
            # example: https://api.ston.fi/v1/stats/asset/EQA2kCVNwVsil2EM2mB0SkXytxCqQjS4mttjDpnXmwG9T6bO/holders?with_staked=true&timestamp=2025-01-16T01:00:00
            res = requests_retry_session().get(
                STONFI_ENDPOINT + "/v1/stats/asset/" + token_address + "/holders",
                params={
                    "with_staked": "true",
                    "timestamp": target_date
                },
                timeout=60,
            )
            payload = res.json()

            if "holders" in payload and len(payload["holders"]) > 0:
                for holder in payload["holders"]:
                    wallet_address = holder["wallet_address"]
                    block_data[wallet_address] = int(holder["total_amount"]) / token_decimals_base
        except Exception as e:
            # pylint: disable=line-too-long
            err_msg = f"Error getting participants data for STON.fi L2 delegation at block {block}: {e}"
            logging.error(err_msg)
            slack_message(err_msg)

        return block_data


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
        blocks=[21671160, 21683570],
    )

    print("=" * 120)
    print("Run without cached data", json.dumps(stonfi_integration_output, indent=2))
    print("=" * 120, "\n" * 5)
