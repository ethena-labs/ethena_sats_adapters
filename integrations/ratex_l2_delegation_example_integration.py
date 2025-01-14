import logging

from typing import Dict, List, Optional
from constants.example_integrations import RATEX_EXAMPLE_USDE_START_BLOCK
from constants.integration_token import Token
from integrations.l2_delegation_integration import L2DelegationIntegration
from utils.web3_utils import get_block_date
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.integration_ids import IntegrationID
from utils.request_utils import requests_retry_session
from utils.slack import slack_message

RATEX_ENDPOINT = "https://api.rate-x.io/"

TOKEN_TO_METHOD = {
    Token.USDE: "queryUSDEPoints",
    Token.SUSDE: "querySUSDEPoints",
}


def get_ratex_payload(
    trade_date: str, method: str = "queryUSDEPoints", page_num: int = 0
) -> dict:
    return {
        "serverName": "AdminSvr",
        "method": method,
        "content": {
            "cid": "test-1",
            "trade_date": trade_date,
            "page_num": page_num,
            "page_size": 200,
        },
    }


class RatexL2DelegationExampleIntegration(L2DelegationIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        summary_cols: Optional[List[SummaryColumn]] = None,
        chain: Chain = Chain.SOLANA,
        reward_multiplier: int = 1,
        end_block: Optional[int] = None,
    ):

        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=(
                summary_cols
                if summary_cols
                else [
                    SummaryColumn.RATEX_EXAMPLE_PTS,
                ]
            ),
            reward_multiplier=reward_multiplier,
            end_block=end_block,
        )
        self.token = integration_id.get_token()

    def get_l2_block_balances(
        self, cached_data: Dict[int, Dict[str, float]], blocks: List[int]
    ) -> Dict[int, Dict[str, float]]:
        logging.info(
            f"Getting block data for Ratex L2 delegation example and blocks {blocks}..."
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
        logging.info(
            f"Fetching participants data for Ratex L2 delegation example at block {block}..."
        )
        block_data: Dict[str, int | float] = {}
        target_date = get_block_date(block, self.chain, adjustment=3600)
        page_num = 0
        while True:
            try:
                res = requests_retry_session().get(
                    RATEX_ENDPOINT,
                    json=get_ratex_payload(
                        trade_date=target_date,
                        method=TOKEN_TO_METHOD[self.token],
                        page_num=page_num,
                    ),
                    timeout=60,
                )
                response = res.json()
                if "data" not in response or len(response["data"]) == 0:
                    break
                for pos_data in response["data"]:
                    if (
                        pos_data["market_indicator"].upper()
                        != self.integration_id.get_token().value.upper()
                    ):
                        continue
                    user_address = pos_data["user_id"]
                    block_data[user_address] = round(pos_data["token_amount"], 4)
                page_num += 1
            except Exception as e:
                err_msg = f"Error getting participants data for Ratex L2 delegation example: {e}"
                logging.error(err_msg)
                slack_message(err_msg)
                break

        return block_data


if __name__ == "__main__":
    example_integration = RatexL2DelegationExampleIntegration(
        integration_id=IntegrationID.RATEX_USDE_EXAMPLE,
        start_block=RATEX_EXAMPLE_USDE_START_BLOCK,
        summary_cols=[
            SummaryColumn.RATEX_EXAMPLE_PTS,
        ],
        chain=Chain.SOLANA,
        reward_multiplier=1,
    )

    example_integration_output = example_integration.get_l2_block_balances(
        cached_data={}, blocks=[21209856, 21217056]
    )

    print("=" * 120)
    print("Run without cached data", example_integration_output)
    print("=" * 120, "\n" * 5)
