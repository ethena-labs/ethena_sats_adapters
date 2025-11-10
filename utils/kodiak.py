from copy import deepcopy
import json
from typing import Dict, List
from eth_typing import ChecksumAddress
import requests
from constants.chains import Chain
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from constants.kodiak import KODIAK_API_URL, KodiakIslandAddress, Tokens

BASE_URL = f"{KODIAK_API_URL}/balances"

class KodiakIntegration(Integration):

    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain,
    ):
        if chain not in [Chain.BERACHAIN]:
            raise ValueError(f"KodiakIntegration not supported on chain {chain}")
        
        if integration_id is IntegrationID.KODIAK_USDE:
            self.island = KodiakIslandAddress.USDE
            self.token = Tokens.USDE
        elif integration_id is IntegrationID.KODIAK_SUSDE:
            self.island = KodiakIslandAddress.SUSDE
            self.token = Tokens.SUSDE
        else:
            raise ValueError(f"KodiakIntegration does not support integration ID {integration_id}")

        super().__init__(
            integration_id,
            start_block,
            chain
        )
        
    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """
        Get the balances of all users at the given blocks
        """
        base_url = f"{BASE_URL}/{self.token.value.lower()}"

        result = {}
        for block in blocks:
            if block in cached_data:
                result[block] = deepcopy(cached_data[block])
                continue

            params = {"excludeSources": "balance", "blockNumber": block}
            response = requests.get(base_url, params=params)
            data = response.json()

            block_data = {}
            for entry in data:
                user_address = ChecksumAddress(entry["id"])
                value = 0.0
                for balance_entry in entry["_sources"]:
                    if "extraData" in balance_entry:
                        extra_data = balance_entry["extraData"]
                        if extra_data.get("islandId") == self.island.value.lower():
                            value += float(balance_entry["value"])
                    elif balance_entry["source"] == "v3-position":
                        value += float(balance_entry["value"])
                            
                if value > 0:
                    block_data[user_address] = value
            result[block] = block_data
        
        return result
