import json
from web3 import Web3
from utils.web3_utils import w3

with open("abi/ERC20_abi.json") as f:
    ERC20_ABI = json.load(f)

PAGINATION_SIZE = 2000
SZSUSDE_ADDRESS = Web3.to_checksum_address(
    "0xb17FB6d8ACa02981FEC71b3624234c9Bcd8F0Ce8"
)
SZSUSDE_START_BLOCK = 21580966
SZSUSDE_CONTRACT = w3.eth.contract(
    address=SZSUSDE_ADDRESS,
    abi=ERC20_ABI,
)
