import logging
from copy import deepcopy
from typing import Dict, List

from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.termmax import CHAIN_TO_CONFIG_MAP
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.request_utils import requests_retry_session


class TermmaxCachedBalancesIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain,
        reward_multiplier: int = 1,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            reward_multiplier=reward_multiplier,
        )

    @property
    def _chain_id(self) -> str:
        return CHAIN_TO_CONFIG_MAP[self.chain]["chain_id"]

    @property
    def _token_address(self) -> ChecksumAddress:
        return CHAIN_TO_CONFIG_MAP[self.chain]["token_to_config_map"][
            self.integration_id.value[2]
        ]["address"]

    @property
    def _data_manager_api_origin(self) -> str:
        return CHAIN_TO_CONFIG_MAP[self.chain]["data_manager_api_origin"]

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        block_number_to_account_address_to_balance_map = deepcopy(cached_data)
        for block in blocks:
            if block not in block_number_to_account_address_to_balance_map:
                block_number_to_account_address_to_balance_map[block] = (
                    self._get_account_address_to_balance_map_for_block(
                        block_id=f"{block}"
                    )
                )
        return block_number_to_account_address_to_balance_map

    def _get_account_address_to_balance_map_for_block(
        self, block_id: str
    ) -> Dict[ChecksumAddress, float]:
        logging.info(f"[Termmax integration] [Block {block_id}] Getting balances...")
        try:
            account_addresses = self._get_account_addresses_for_block(block_id)
            if len(account_addresses) == 0:
                return {}
            response = requests_retry_session().get(
                f"{self._data_manager_api_origin}/v1/integrations/ethena/effective_balances",
                params={
                    "chain_id": self._chain_id,
                    "block_id": block_id,
                    "token_addresses": [self._token_address],
                    "account_addresses": account_addresses,
                },
            )
            return {
                Web3.to_checksum_address(
                    effective_balance_dict["account_address"]
                ): float(effective_balance_dict["balance"])
                for effective_balance_dict in response.json()["data"][
                    "effective_balances"
                ]
            }
        except Exception as e:
            logging.error(
                f"[Termmax integration] [Block {block_id}] Error getting balances: {e}"
            )
            raise e

    def _get_account_addresses_for_block(self, block_id: str) -> List[ChecksumAddress]:
        logging.info(
            f"[Termmax integration] [Block {block_id}] Getting account addresses..."
        )
        try:
            response = requests_retry_session().get(
                f"{self._data_manager_api_origin}/v1/integrations/ethena/effective_accounts",
                params={
                    "chain_id": self._chain_id,
                    "block_id": block_id,
                    "token_addresses": [self._token_address],
                },
            )
            return [
                Web3.to_checksum_address(effective_account_dict["account_address"])
                for effective_account_dict in response.json()["data"][
                    "effective_accounts"
                ]
            ]
        except Exception as e:
            logging.error(
                f"[Termmax integration] [Block {block_id}] Error getting account addresses: {e}"
            )
            raise e


if __name__ == "__main__":
    integration = TermmaxCachedBalancesIntegration(
        integration_id=IntegrationID.TERMMAX_SUSDE,
        start_block=CHAIN_TO_CONFIG_MAP[Chain.ETHEREUM]["token_to_config_map"][
            IntegrationID.TERMMAX_SUSDE.value[2]
        ]["start_block"],
        chain=Chain.ETHEREUM,
    )
    balances = integration.get_block_balances(
        cached_data={}, blocks=[22174000, 22174001, 22174002]
    )
    print(balances)
