import json
from utils.web3_utils import (
    w3_mantle,
)

from constants.lendle import LENDLE_USDE

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


lendle_usde_contract = w3_mantle.eth.contract(address=LENDLE_USDE, abi=erc20_abi)

