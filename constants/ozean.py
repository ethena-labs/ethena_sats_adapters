import json
from pathlib import Path
from web3 import Web3
from utils.web3_utils import W3_BY_CHAIN
from constants.chains import Chain

with open(Path(__file__).parent.parent / "abi" / "ozean_lge.json", "r") as f:
    LGE_ABI = json.load(f)

LGE_CONTRACT_ADDRESS = Web3.to_checksum_address("0xdD4297dECCE33fdA78dB8330832b51F3df610db9")

SUSDE_TOKEN_ADDRESS = Web3.to_checksum_address("0x9D39A5DE30e57443BfF2A8307A4256c8797A3497")

OZEAN_LGE_DEPLOYMENT_BLOCK = 21893208

PAGINATION_SIZE = 2000

LGE_CONTRACT = W3_BY_CHAIN[Chain.SEPOLIA]["w3"].eth.contract(
    address=LGE_CONTRACT_ADDRESS,
    abi=LGE_ABI
) 