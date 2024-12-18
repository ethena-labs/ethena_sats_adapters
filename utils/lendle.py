import json
from web3.contract import Contract
from web3 import Web3
from utils.web3_utils import (
    w3_mantle,
)

from constants.lendle import LENDLE_USDE_TOKEN
from constants.lendle import LENDLE_SUSDE_TOKEN

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


lendle_usde_contract: Contract = w3_mantle.eth.contract(
    address=Web3.to_checksum_address(LENDLE_USDE_TOKEN), abi=erc20_abi
)

lendle_susde_contract: Contract = w3_mantle.eth.contract(
    address=Web3.to_checksum_address(LENDLE_SUSDE_TOKEN), abi=erc20_abi
)
