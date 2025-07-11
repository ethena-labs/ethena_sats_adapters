import json
from typing import Dict, List, Optional, Tuple

from constants.affluent import AFFLUENT_ENDPOINT, AFFLUENT_USDE_START_BLOCK, AFFLUENT_SUSDE_START_BLOCK, TOKEN_ADDRESS_MAP

from integrations.l2_delegation_integration import L2DelegationIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import get_block_date
from utils.request_utils import requests_retry_session
from utils.slack import slack_message
from constants.summary_columns import SummaryColumn
from constants.chains import Chain

class AffluentIntegration(L2DelegationIntegration):
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
             summary_cols=summary_cols if summary_cols else [SummaryColumn.AFFLUENT_USDE_PTS],
             reward_multiplier=reward_multiplier,
             end_block=end_block,
         )

    def get_l2_block_balances(
         self,
         cached_data: Dict[int, Dict[str, float]],
         blocks: List[int]
     ) -> Dict[int, Dict[str, float]]:
        try:
            block_balances: Dict[int, Dict[str, float]] = {}

            for target_block in blocks:
                block_balances[target_block] = self.get_participants_data(target_block)

            return block_balances
        except Exception as e:
            err_msg = f"Error fetching Affluent balances at block {target_block}: {e}"
            print(err_msg)
            slack_message(err_msg)

    def get_token_symbol(self):
         return self.integration_id.get_token()

    def get_participants_data(self, block: int) -> Dict[str, float]:
        token = self.get_token_symbol()
        token_address = TOKEN_ADDRESS_MAP[token]
        block_data: Dict[str, float] = {}
        target_date = get_block_date(block, self.chain, adjustment=3600, fmt="%Y-%m-%dT%H:%M:%S")

        try:
            res = requests_retry_session().get(
                AFFLUENT_ENDPOINT + "/holdings",
                params={
                    "assets": token_address,
                    "timestamp": target_date,
                },
                timeout=60,
            )
            payload = res.json()

            if payload is None:
                raise Exception(f"Error getting participants data for Affluent Protocol token {token} at block {block}: {e}")
            
            for user_data in payload["result"]:
                block_data[user_data["user_address"]] = user_data["balance"]

        except Exception as e:
                err_msg = f"Error getting participants data for Affluent Protocol at block {block}: {e}"
                slack_message(err_msg)

        return block_data


if __name__ == "__main__":
    affluent_integration_usde = AffluentIntegration(
        integration_id=IntegrationID.AFFLUENT_USDE,
        start_block=AFFLUENT_USDE_START_BLOCK,
        summary_cols=[SummaryColumn.AFFLUENT_USDE_PTS],
        chain=Chain.TON,
        reward_multiplier=20
    )
    affluent_integration_susde = AffluentIntegration(
        integration_id=IntegrationID.AFFLUENT_SUSDE,
        start_block=AFFLUENT_SUSDE_START_BLOCK,
        summary_cols=[SummaryColumn.AFFLUENT_SUSDE_PTS],
        chain=Chain.TON,
        reward_multiplier=5
    )

    print("Affluent USDe  :", json.dumps(affluent_integration_usde.get_l2_block_balances(cached_data={}, blocks=[22895215, 22895215 - 600]), indent=2))
    print("Affluent sUSDe :", json.dumps(affluent_integration_susde.get_l2_block_balances(cached_data={}, blocks=[22895215]), indent=2))

