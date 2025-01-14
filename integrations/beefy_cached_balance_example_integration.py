import logging

from constants.example_integrations import (
    BEEFY_ARBITRUM_START_BLOCK_EXAMPLE,
)
from integrations.cached_balances_integration import CachedBalancesIntegration
from web3 import Web3
from constants.chains import Chain
from typing import Dict, List, Set, cast
from eth_typing import ChecksumAddress

from constants.beefy import BEEFY_LRT_API_URL
from constants.summary_columns import SummaryColumn
from integrations.integration_ids import IntegrationID
from utils.request_utils import requests_retry_session
from utils.slack import slack_message

CHAIN_TO_API_URL_PREFIX = {
    Chain.ARBITRUM: f"{BEEFY_LRT_API_URL}/partner/ethena/arbitrum",
    Chain.FRAXTAL: f"{BEEFY_LRT_API_URL}/partner/ethena/fraxtal",
    Chain.MANTLE: f"{BEEFY_LRT_API_URL}/partner/ethena/mantle",
    Chain.OPTIMISM: f"{BEEFY_LRT_API_URL}/partner/ethena/optimism",
}


class BeefyCachedBalanceIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain,
        summary_cols: List[SummaryColumn],
        reward_multiplier: int = 1,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            balance_multiplier=1,
            excluded_addresses=None,
            end_block=None,
        )

    def get_beefy_users(self) -> Set[ChecksumAddress]:
        """
        Get all participants of the protocol, ever.
        """
        logging.info("[Beefy integration] Getting participants...")
        try:
            base_url = CHAIN_TO_API_URL_PREFIX[self.chain]
            url = f"{base_url}/users"

            response = requests_retry_session().get(url)
            data = cast(List[str], response.json())
            return set(Web3.to_checksum_address(user) for user in data)
        except Exception as e:
            msg = f"Error getting participants for beefy: {e}"
            logging.error(msg)
            slack_message(msg)
            return set()

    def get_data_for_block(
        self, block: int, users: Set[ChecksumAddress]
    ) -> Dict[ChecksumAddress, float]:
        logging.info(f"Getting data for beefy at block {block}...")

        if block < self.start_block:
            return {}
        data: Dict[ChecksumAddress, float] = {}
        # Just get the first 10 users as a quick example
        for user in list(users)[:10]:
            try:
                base_url = CHAIN_TO_API_URL_PREFIX[self.chain]
                url = f"{base_url}/user/{user}/balance/{block}"
                response = requests_retry_session(retries=1, backoff_factor=0).get(url)
                user_data = response.json()

                if user_data is None or "effective_balance" not in user_data:
                    data[user] = 0.0
                data[user] = round(float(user_data["effective_balance"]), 4)
            except Exception as e:
                msg = f"Error getting beefy data for {user} at block {block}: {e}"
                logging.error(msg)
                slack_message(msg)
                data[user] = 0.0
        return data

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block data for beefy...")
        block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        beefy_users = self.get_beefy_users()
        for block in blocks:
            if block < self.start_block:
                block_data[block] = {}
                continue
            block_data[block] = self.get_data_for_block(block, beefy_users)
        return block_data


if __name__ == "__main__":
    example_integration = BeefyCachedBalanceIntegration(
        integration_id=IntegrationID.BEEFY_CACHED_BALANCE_EXAMPLE,
        start_block=BEEFY_ARBITRUM_START_BLOCK_EXAMPLE,
        chain=Chain.ARBITRUM,
        summary_cols=[SummaryColumn.BEEFY_CACHED_BALANCE_EXAMPLE],
    )
    # Since this integration is based on API calls, we don't need to use the cached data
    print(example_integration.get_block_balances(cached_data={}, blocks=[276231389]))
