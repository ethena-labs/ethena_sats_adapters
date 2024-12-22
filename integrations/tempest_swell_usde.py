import logging
import json
from copy import deepcopy

from integrations.cached_balances_integration import CachedBalancesIntegration
from web3 import Web3
from constants.chains import Chain
from typing import Dict, List, Set
from eth_typing import ChecksumAddress
from utils.web3_utils import (
    W3_BY_CHAIN,
    MULTICALL_ADDRESS_BY_CHAIN,
    multicall_by_address
)

import constants.tempest as c
from constants.summary_columns import SummaryColumn
from integrations.integration_ids import IntegrationID
from utils.request_utils import requests_retry_session

class TempestCachedBalanceIntegration(CachedBalancesIntegration):
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
        self.vault_contract_by_address = {}
        self.w3 = W3_BY_CHAIN[self.chain]["w3"]
        with open(c.ABI_FILENAME, "r") as f:
            abi = json.load(f)
            for vault in c.VAULTS:
                self.vault_contract_by_address[vault.address] = self.w3.eth.contract(
                    address=Web3.to_checksum_address(vault.address), abi=abi
                )
        self.multicall_address = MULTICALL_ADDRESS_BY_CHAIN[chain]

    def get_tempest_users(self, vault_address: str) -> Set[ChecksumAddress]:
        """
        Get all users of the vault.
        """
        logging.info("[Tempest integration] Getting users...")
        try:
            response = requests_retry_session().get(c.GET_USERS_API_URL, params={"chainId": c.CHAIN_ID_SWELL, "vaultAddresses": vault_address})
            data = response.json()["data"]
            return set(Web3.to_checksum_address(user) for user in data["userAddresses"])
        except Exception as e:
            msg = f"Error getting users for Tempest: {e}"
            logging.error(msg)
            return set()

    def get_data_for_block(
        self, block: int, vault_address: str, genesis_block: int
    ) -> Dict[ChecksumAddress, float]:
        logging.info(f"Getting data for Tempest at block {block}...")

        if block <= genesis_block:
            return {}
        
        contract = self.vault_contract_by_address[vault_address]
        
        # get share balance of all users
        data: Dict[ChecksumAddress, float] = {}
        users = list(self.get_tempest_users(vault_address))
        if len(users) == 0:
            return data
        balance_of_calls = [
            (contract, contract.functions.balanceOf.fn_name, [user])
            for user in users
        ]
        balance_of_results = multicall_by_address(self.w3, self.multicall_address, balance_of_calls, block)
        
        # get vault totalAssets and totalSupply
        vault_calls = [(contract, contract.functions.getPositions.fn_name, None), (contract, contract.functions.totalSupply.fn_name, None)]
        vault_results = multicall_by_address(self.w3, self.multicall_address, vault_calls, block)
        # vault_results[0][0] is USDe in Ambient positions, vault_results[0][2] is idle USDe in the vault
        total_usde = vault_results[0][0] + vault_results[0][2] 
        total_supply = vault_results[1][0]
        
        # convert share balance to USDe balance
        for i in range(0, len(users)):
            if balance_of_results[i][0] == 0:
                continue
            data[users[i]] = balance_of_results[i][0] * total_usde / total_supply
        
        return data

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block data for Tempest...")
        data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to Tempest Swell USDe get_block_balances")
            return data
        data = deepcopy(cached_data)
        for vault in c.VAULTS:
            for block in blocks:
                if cached_data != None and cached_data.get(block) != None:
                    continue
                vault_data = self.get_data_for_block(block, vault_address=vault.address, genesis_block=vault.genesis_block)
                for user, balance in vault_data.items():
                    if block not in data:
                        data[block] = {}
                    if user not in data[block]:
                        data[block][user] = balance
                    else:
                        data[block][user] += balance
        return data

if __name__ == "__main__":
    integration = TempestCachedBalanceIntegration(
        integration_id=IntegrationID.TEMPEST_SWELL_USDE,
        start_block=0,
        chain=Chain.SWELL,
        summary_cols=[SummaryColumn.TEMPEST_SWELL_SHARDS],
    )
    balances = integration.get_block_balances(cached_data={}, blocks=[983436])
    print(balances)
