import json
from web3 import Web3
from utils.web3_utils import w3_berachain

PAGINATION_SIZE = 1000
BEND_ADDRESS = Web3.to_checksum_address("0x24147243f9c08d835C218Cda1e135f8dFD0517D0")

with open("abi/morpho.json") as f:
    BEND_ABI = json.load(f)

BEND_CONTRACT = w3_berachain.eth.contract(
    address=BEND_ADDRESS,
    abi=BEND_ABI,
)

BEND_MARKET_IDS = [
    "0x1ba7904c73d337c39cb88b00180dffb215fc334a6ff47bbe829cd9ee2af00c97",
]

# NOTE: per https://berascan.com/tx/0x14a3eddaa857a67b1c8cb143280b506617e191374810d41b3ffeef58c5d0a7bf, the first deployment tx
BEND_SUSDE_SUSDS_START_BLOCK = 11572788
