import json
from typing import TypedDict, Dict
from utils.web3_utils import W3_BY_CHAIN
from web3.contract.contract import Contract
from web3 import Web3
from constants.chains import Chain
from integrations.integration_ids import IntegrationID

with open("abi/radiant_r_token.json") as f:
    r_token_abi = json.load(f)
with open("abi/radiant_lending_pool.json") as f:
    lending_pool_abi = json.load(f)


class RadiantLendingDetails(TypedDict):
    start: int
    chain: Chain
    collateral_address: str
    r_token_contract: Contract
    lending_pool: Contract
    graph_url: str


RADIANT_CONTRACTS_AND_START_BY_TOKEN: Dict[IntegrationID, RadiantLendingDetails] = {
    IntegrationID.RADIANT_USDE_CORE_ARBITRUM: RadiantLendingDetails(
        start=247318247,
        chain=Chain.ARBITRUM,
        collateral_address=Web3.to_checksum_address(
            "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"
        ),
        r_token_contract=W3_BY_CHAIN[Chain.ARBITRUM]["w3"].eth.contract(
            address=Web3.to_checksum_address(
                "0x19f0bE6a603967c72bE32a30915a38d52cA31Ae2"
            ),
            abi=r_token_abi,
        ),
        lending_pool=W3_BY_CHAIN[Chain.ARBITRUM]["w3"].eth.contract(
            address=Web3.to_checksum_address(
                "0xF4B1486DD74D07706052A33d31d7c0AAFD0659E1"
            ),
            abi=lending_pool_abi,
        ),
        graph_url="https://gateway-arbitrum.network.thegraph.com/api/8d1d947ce53cce677d86d075396ad13b/subgraphs/id/E1UTUGaNbTb4XbEYoupJZ5hU62hW9CnadKTXLRSP2hM",
    ),
}
