import json
from typing import TypedDict, Dict
from utils.web3_utils import W3_BY_CHAIN
from web3.contract.contract import Contract
from web3 import Web3
from constants.chains import Chain
from integrations.integration_ids import IntegrationID

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


class StrategyConfig(TypedDict):
    start: int
    chain: Chain
    underlying: Contract
    strategy: Contract
    page_size: int


contract = W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.contract

ALLSTAKE_STRATEGIES: Dict[IntegrationID, StrategyConfig] = {
    IntegrationID.ALLSTAKE_USDE: StrategyConfig(
        start=20810640,
        chain=Chain.ETHEREUM,
        underlying=contract(
            address=Web3.to_checksum_address(
                "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"
            ),
            abi=erc20_abi,
        ),
        strategy=contract(
            address=Web3.to_checksum_address(
                "0x8B6bF38B812BE4749577303FB8D222576957ff44"
            ),
            abi=erc20_abi,
        ),
        page_size=5000,
    ),
    IntegrationID.ALLSTAKE_SUSDE: StrategyConfig(
        start=20811020,
        chain=Chain.ETHEREUM,
        underlying=contract(
            address=Web3.to_checksum_address(
                "0x9d39a5de30e57443bff2a8307a4256c8797a3497"
            ),
            abi=erc20_abi,
        ),
        strategy=contract(
            address=Web3.to_checksum_address(
                "0x5d083d71F7A531F543070b78740880F5A346B53a"
            ),
            abi=erc20_abi,
        ),
        page_size=5000,
    ),
}
