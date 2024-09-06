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
        start=20662600,
        chain=Chain.ETHEREUM,
        underlying=contract(
            address=Web3.to_checksum_address("0x7a56e1c57c7475ccf742a1832b028f0456652f97"), abi=erc20_abi
        ),  # USDe "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"
        strategy=contract(
            address=Web3.to_checksum_address("0x89D7A43659f2Cb2bee432267DFA3fE1cd5Dd6E4B"), abi=erc20_abi
        ),
        page_size=5000,
    ),
    IntegrationID.ALLSTAKE_SUSDE: StrategyConfig(
        start=20662810,
        chain=Chain.ETHEREUM,
        underlying=contract(
            address=Web3.to_checksum_address("0xd9d920aa40f578ab794426f5c90f6c731d159def"), abi=erc20_abi
        ),  # sUSDe "0x9d39a5de30e57443bff2a8307a4256c8797a3497"
        strategy=contract(
            address=Web3.to_checksum_address("0xA0Be838Af5a6D6CAe534a83FA8cEc527A4EBcDe4"), abi=erc20_abi
        ),
        page_size=5000,
    ),
}
