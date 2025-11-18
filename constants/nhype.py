import json

from web3 import Web3

from constants.chains import Chain
from utils.web3_utils import W3_BY_CHAIN

# Load the ERC20 ABI for nHYPE token
with open("abi/ERC20_abi.json") as f:
    nhype_abi = json.load(f)

# nHYPE LST token contract address on HyperEVM
NHYPE_CONTRACT_ADDRESS = Web3.to_checksum_address("0x88888884cdc539d00dfb9C9e2Af81baA65fDA356")

# nHYPE contract instance
NHYPE_CONTRACT = W3_BY_CHAIN[Chain.HYPEREVM]["w3"].eth.contract(
    address=NHYPE_CONTRACT_ADDRESS,
    abi=nhype_abi,
)
