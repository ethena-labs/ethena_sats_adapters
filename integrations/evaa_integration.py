from typing import Dict, List, Optional, Tuple

from constants.evaa import EVAA_POOLS_MAP, EVAA_ENDPOINT, EVAA_USDE_START_BLOCK

from integrations.l2_delegation_integration import L2DelegationIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import get_block_date
from utils.request_utils import requests_retry_session
from utils.slack import slack_message

class EvaaIntegration(L2DelegationIntegration):
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
             summary_cols=summary_cols if summary_cols else [SummaryColumn.EVAA_USDE_PTS],
             reward_multiplier=reward_multiplier,
             end_block=end_block,
         )

    def get_l2_block_balances(
         self,
         cached_data: Dict[int, Dict[str, float]],
         blocks: List[int]
     ) -> Dict[int, Dict[str, float]]:
        """
        Returns a dict of the form: { block_number: { ton_address: balance } }
        """
        try:
            block_balances: Dict[int, Dict[str, float]] = {}

            for block_number in blocks:
                block_balances[block_number] = {}
                block_data = self.get_participants_data(block_number)
                for participant in block_data:
                    ton_address = participant["ton_address"]
                    balance = participant["balance"]
                    block_balances[block_number][ton_address] = balance

            return block_balances
        except Exception as e:
            err_msg = f"Error fetching EVAA balances at block {block_number}: {e}"
            print(err_msg)
            slack_message(err_msg)

    def get_token_symbol(self):
         return self.integration_id.get_token()

    def get_participants_data(self, block: int) -> Dict[str, float]:
        """
        Returns a list of "ton_address": "balance"
        """

        token = self.get_token_symbol()
        pools_list = EVAA_POOLS_MAP[token]
        block_data: Dict[str, float] = {}
        target_date = get_block_date(block, self.chain, adjustment=3600, fmt="%Y-%m-%dT%H:%M:%S")


        try:
            for pool in pools_list:
                res = requests_retry_session().get(
                    EVAA_ENDPOINT + "/query/adapters/ethena",
                    params={
                        "pool_address": pool,
                        "timestamp": target_date
                    },
                    
                    timeout=60,
                )
                payload = res.json()

                if payload is None:
                    raise Exception(f"Error getting participants data for EVAA Protocol token {token} at block {block}: {e}")

                block_data = payload

        except Exception as e:
                err_msg = f"Error getting participants data for EVAA Protocol at block {block}: {e}"
                slack_message(err_msg)

        return block_data


if __name__ == "__main__":
    evaa_integration = EvaaIntegration(
        integration_id=IntegrationID.EVAA_TON_USDE,
        start_block=EVAA_USDE_START_BLOCK,
        summary_cols=[SummaryColumn.EVAA_USDE_PTS],
        chain=Chain.TON,
        reward_multiplier=1,
    ),
    last_block = EVAA_USDE_START_BLOCK
balances = evaa_integration.get_l2_block_balances(
        cached_data={}, blocks=[last_block]
    )
    print(f"Balances at block {last_block}:", balances)

    participants = evaa_integration.get_participants_data(last_block)
    print("Participants:", participants)
