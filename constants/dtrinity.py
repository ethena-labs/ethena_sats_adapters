import json
from web3 import Web3
from utils.web3_utils import w3_fraxtal

# Contract addresses for dTrinity on Fraxtal
LENDING_POOL_ADDRESS = Web3.to_checksum_address("0xD76C827Ee2Ce1E37c37Fc2ce91376812d3c9BCE2")
USDE_ATOKEN_ADDRESS = Web3.to_checksum_address("0x6ae1450d550e44bb014d4c8cd98592863edb0706")
SUSDE_ATOKEN_ADDRESS = Web3.to_checksum_address("0x12ED58F0744dE71C39118143dCc26977Cb99cDef")

# Genesis blocks for dTrinity markets
USDE_GENESIS_BLOCK = 16790827
SUSDE_GENESIS_BLOCK = 13799261

# Load ABIs
with open("abi/dtrinity_atoken.json") as f:
    ATOKEN_ABI = json.load(f)

with open("abi/dtrinity_lending_pool.json") as f:
    LENDING_POOL_ABI = json.load(f)

# Create contract instances
lending_pool_contract = w3_fraxtal.eth.contract(
    address=LENDING_POOL_ADDRESS,
    abi=LENDING_POOL_ABI
)

usde_atoken_contract = w3_fraxtal.eth.contract(
    address=USDE_ATOKEN_ADDRESS,
    abi=ATOKEN_ABI
)

susde_atoken_contract = w3_fraxtal.eth.contract(
    address=SUSDE_ATOKEN_ADDRESS,
    abi=ATOKEN_ABI
) 