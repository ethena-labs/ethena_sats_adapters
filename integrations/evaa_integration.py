from typing import Any, Dict, List, Optional, Tuple

from constants.evaa import EVAA_POOLS_MAP, EVAA_ENDPOINT, EVAA_USDE_START_BLOCK, EVAA_SUSDE_START_BLOCK

from integrations.l2_delegation_integration import L2DelegationIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import get_block_date
from utils.request_utils import requests_retry_session
from utils.slack import slack_message
from constants.summary_columns import SummaryColumn
from constants.chains import Chain
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
                block_balances[block_number] = self.get_participants_data(block_number)

            return block_balances
        except Exception as e:
            err_msg = f"Error fetching EVAA balances: {e}"
            print(err_msg)
            slack_message(err_msg)
            return {}

    def get_token_symbol(self):
         return self.integration_id.get_token()

    def get_participants_data(self, block: int) -> Dict[str, float]:
        """
        Returns a dict mapping ton_address to balance (matches L2DelegationIntegration).
        """
        token = self.get_token_symbol()
        pools_list = EVAA_POOLS_MAP[token]
        block_data: List[Dict[str, Any]] = []
        target_date = get_block_date(block, self.chain, adjustment=3600, fmt="%Y-%m-%dT%H:%M:%S")

        try:
            for pool in pools_list:
                res = requests_retry_session().get(
                    EVAA_ENDPOINT + "/query/adapters/ethena",
                    params={
                        "pool_address": pool,
                        "timestamp": target_date,
                        "token": token.value
                    },
                    timeout=60,
                )
                payload = res.json()

                if payload is None:
                    raise Exception(f"Error getting participants data for EVAA Protocol token {token} at block {block}: empty response")

                if isinstance(payload, list):
                    block_data.extend(payload)
                else:
                    block_data.append(payload)

        except Exception as e:
                err_msg = f"Error getting participants data for EVAA Protocol at block {block}: {e}"
                slack_message(err_msg)

        return {p["ton_address"]: float(p["balance"]) for p in block_data}


if __name__ == "__main__":
    evaa_integration_usde = EvaaIntegration(
        integration_id=IntegrationID.EVAA_TON_USDE,
        start_block=EVAA_USDE_START_BLOCK,
        summary_cols=[SummaryColumn.EVAA_USDE_PTS],
        chain=Chain.TON,
        reward_multiplier=20
    )
    evaa_integration_susde = EvaaIntegration(
        integration_id=IntegrationID.EVAA_TON_SUSDE,
        start_block=EVAA_SUSDE_START_BLOCK,
        summary_cols=[SummaryColumn.EVAA_SUSDE_PTS],
        chain=Chain.TON,
        reward_multiplier=5
    )

    balances_usde = evaa_integration_usde.get_l2_block_balances(
        cached_data={}, blocks=[22596292]
    )
    balances_susde = evaa_integration_susde.get_l2_block_balances(
        cached_data={}, blocks=[22596292]
    )

    print("Balances USDe:", balances_usde)
    print("Balances sUSDe:", balances_susde)
