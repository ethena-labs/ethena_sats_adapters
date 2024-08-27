import json
from typing import TypedDict, Dict
from utils.web3_utils import W3_BY_CHAIN
from web3.contract.contract import Contract
from web3 import Web3
from constants.chains import Chain
from constants.integration_ids import IntegrationID

with open("abi/radiant_r_token.json") as f:
    r_token_abi = json.load(f)
with open("abi/radiant_lending_pool.json") as f:
    lending_pool_abi = json.load(f)


class RadiantLendingDetails(TypedDict):
    start: int
    chain: str
    collateral_address: str
    r_token_contract: Contract
    lending_pool: Contract
    graph_url: str


RADIANT_CONTRACTS_AND_START_BY_TOKEN: Dict[IntegrationID, RadiantLendingDetails] = {
    IntegrationID.RADIANT_USDE_CORE_MAINNET: RadiantLendingDetails(
        start=18466402,
        chain=Chain.ETHEREUM,
        collateral_address= Web3.to_checksum_address("0x35751007a407ca6feffe80b3cb397736d2cf4dbe"),
        r_token_contract=W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.contract(
            address=Web3.to_checksum_address("0xb11a56da177c5532d5e29cc8363d145bd0822c81"), abi=r_token_abi
        ),
        lending_pool=W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.contract(
            address=Web3.to_checksum_address("0xA950974f64aA33f27F6C5e017eEE93BF7588ED07"), abi=lending_pool_abi
        ),
        graph_url="https://gateway-arbitrum.network.thegraph.com/api/8d1d947ce53cce677d86d075396ad13b/subgraphs/id/683Qhh8TEta6qS5gdTpXCs84xnrp77fPWGQyBmRe6qgo",
    ),
    IntegrationID.RADIANT_USDE_CORE_ARBITRUM: RadiantLendingDetails(
        start=247318247,
        chain=Chain.ARBITRUM,
        collateral_address= Web3.to_checksum_address("0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"),
        r_token_contract=W3_BY_CHAIN[Chain.ARBITRUM]["w3"].eth.contract(
            address=Web3.to_checksum_address("0x19f0bE6a603967c72bE32a30915a38d52cA31Ae2"), abi=r_token_abi
        ),
        lending_pool=W3_BY_CHAIN[Chain.ARBITRUM]["w3"].eth.contract(
            address=Web3.to_checksum_address("0xF4B1486DD74D07706052A33d31d7c0AAFD0659E1"), abi=lending_pool_abi
        ),
        graph_url="https://gateway-arbitrum.network.thegraph.com/api/8d1d947ce53cce677d86d075396ad13b/subgraphs/id/E1UTUGaNbTb4XbEYoupJZ5hU62hW9CnadKTXLRSP2hM",
    ),
}

