import json
from typing import TypedDict, Dict
from utils.web3_utils import W3_BY_CHAIN
from web3.contract.contract import Contract
from web3 import Web3
from constants.chains import Chain
from constants.integration_ids import IntegrationID

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


class StrategyConfig(TypedDict):
    start: int
    chain: str
    underlying: Contract
    strategy: Contract
    page_size: int

contract = W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.contract

ALLSTAKE_STRATEGIES: Dict[IntegrationID, StrategyConfig] = {
    # TODO: Replace with actual USDe and sUSDe tokens and strategies. The current config is for testing only.
    IntegrationID.ALLSTAKE_USDE: StrategyConfig(
        start=20690635,
        chain=Chain.ETHEREUM,
        underlying=contract(
            address=Web3.to_checksum_address("0x4c9edd5852cd905f086c759e8383e09bff1e68b3"), abi=erc20_abi
        ),
        strategy=contract(
            address=Web3.to_checksum_address("0x69bb6ae7db9cca28d24aeda5a432bc2f932f2183"), abi=erc20_abi
        ), # staging AUSDe contract
        page_size=5000,
    ),
    IntegrationID.ALLSTAKE_SUSDE: StrategyConfig(
        start=20690660,
        chain=Chain.ETHEREUM,
        underlying=contract(
            address=Web3.to_checksum_address("0x9d39a5de30e57443bff2a8307a4256c8797a3497"), abi=erc20_abi
        ),
        strategy=contract(
            address=Web3.to_checksum_address("0x4e78c5e7f52ae8e34693584fc2103c58018adde2"), abi=erc20_abi
        ), # staging AsUSDe contract
        page_size=5000,
    ),
}
