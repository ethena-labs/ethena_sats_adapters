from copy import deepcopy
import logging

from typing import Dict, List
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from constants.termmax import CHAIN_TO_CONFIG_MAP
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress

from utils.request_utils import requests_retry_session


class TermMaxPtSusde25Sep2025(CachedBalancesIntegration):
    """
    TermMax PT-sUSDE-25SEP2025 Collateral Integration
    """
    def __init__(self):
        super().__init__(
            integration_id=IntegrationID.TERMMAX_PT_SUSDE_25SEP2025,
            start_block=CHAIN_TO_CONFIG_MAP[Chain.ETHEREUM]["token_to_config_map"][
                IntegrationID.TERMMAX_PT_SUSDE_25SEP2025.value[2]
            ]["start_block"],
            chain=Chain.ETHEREUM,
            summary_cols=[SummaryColumn.TERMMAX_PT_SUSDE_25SEP2025_PTS],
            reward_multiplier=1,
            balance_multiplier=1,
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
        logging.info(f"[TermMax integration] Getting block data for PT-sUSDE-25SEP2025 collateral...")
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
        logging.info(f"[TermMax integration] [Block {block_id}] Getting balances...")
        try:
            account_addresses = self._get_account_addresses_for_block(block_id)
            if len(account_addresses) == 0:
                return {}
            response = requests_retry_session().get(
                f"{self._data_manager_api_origin}/v1/integrations/ethena/pt_susde_25sep2025_effective_balances",
                params={
                    "block_id": block_id,
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
                f"[TermMax integration] [Block {block_id}] Error getting balances: {e}"
            )
            raise e

    def _get_account_addresses_for_block(self, block_id: str) -> List[ChecksumAddress]:
        logging.info(
            f"[TermMax integration] [Block {block_id}] Getting account addresses..."
        )
        try:
            response = requests_retry_session().get(
                f"{self._data_manager_api_origin}/v1/integrations/ethena/pt_susde_25sep2025_effective_accounts",
                params={
                    "block_id": block_id,
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
                f"[TermMax integration] [Block {block_id}] Error getting account addresses: {e}"
            )
            raise e


if __name__ == "__main__":
    integration = TermMaxPtSusde25Sep2025()
    print(
        integration.get_block_balances(
            cached_data={}, blocks=[22886966, 22890231]
        )
    )
    # Example output:
    # {
    #     "22886966":{},
    #     "22890231":{
    #         "0xF82f8d46B175827Fb4f6bEbeFF846cE0c4d0A90e": 5.06916e+18,
    #     }
    # }

    print(
        integration.get_block_balances(
            cached_data={
                22886966: {},
            },
            blocks=[22890231],
        )
    )
    # Example output:
    # {
    #   22890231: {
    #     "0xF82f8d46B175827Fb4f6bEbeFF846cE0c4d0A90e": 5.06916e+18,
    #   }
    # }
  
