from typing import Dict, List
from eth_typing import ChecksumAddress
from constants.summary_columns import SummaryColumn
from constants.chains import Chain
from constants.euler import MAINNET_MAXI_SUSDE_URL
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID as IntID
from utils.request_utils import requests_retry_session


class EulerMainnetMaxiSUSDEIntegration(CachedBalancesIntegration):
    def __init__(self):
        super().__init__(
            integration_id=IntID.EULER_MAINNET_MAXI_SUSDE,
            start_block=20684113,
            chain=Chain.ETHEREUM,
            summary_cols=[SummaryColumn.EULER_MAINNET_MAXI_SUSDE_PTS],
            reward_multiplier=5,
            balance_multiplier=1,
            excluded_addresses=None,
            end_block=None,
            ethereal_multiplier=0,
            ethereal_multiplier_func=None,
        )

    def get_data_for_block(self, block: int) -> Dict[ChecksumAddress, float]:
        if block < self.start_block:
            return {}
        url = f"{MAINNET_MAXI_SUSDE_URL}?blockNumber={block}"
        response = requests_retry_session(retries=3).get(url)
        data = response.json()
        
        # Transform the data into the required format
        result = {}
        if "Result" in data and isinstance(data["Result"], list):
            for item in data["Result"]:
                balance = float(item["effective_balance"])
                result[item["address"]] = balance
        
        return result

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        for block in blocks:
            if block < self.start_block:
                block_data[block] = {}
                continue
            block_data[block] = self.get_data_for_block(block)
        return block_data
