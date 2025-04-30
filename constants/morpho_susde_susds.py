import json
from web3 import Web3
from utils.web3_utils import w3

PAGINATION_SIZE = 2000
MORPHO_ADDRESS = Web3.to_checksum_address("0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb")
with open("abi/morpho.json") as f:
    MORPHO_ABI = json.load(f)

MORPHO_CONTRACT = w3.eth.contract(
    address=MORPHO_ADDRESS,
    abi=MORPHO_ABI,
)

MORPHO_MARKET_IDS = [
    "0xe0800b3f305b167e65738adc54e03d48c7bf4fb03af2734b4a72034852ba4a7a",
]

# NOTE: per https://etherscan.io/tx/0x079b93a9b2f7ce98b8be93e3af103cc38550203a5a562dda5279925cf1bae9c3, the first deployment tx
MORPHO_SUSDE_SUSDS_START_BLOCK = 22479246
