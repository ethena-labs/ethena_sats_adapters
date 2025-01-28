import json
from web3 import Web3
from constants.chains import Chain
from utils.web3_utils import (
    w3,
    w3_sepolia,
)

PAGINATION_SIZE = 2000

with open("abi/cork_module_core.json") as f:
    MODULE_CORE_ABI = json.load(f)

PSM_ADDRESS_BY_CHAIN = {
    Chain.ETHEREUM: Web3.to_checksum_address("0x57e114B691Db790C35207b2e685D4A43181e6061"),
    Chain.SEPOLIA: Web3.to_checksum_address("0x57e114B691Db790C35207b2e685D4A43181e6061"),
}

PSM_CONTRACT_BY_CHAIN = {
    Chain.ETHEREUM: w3.eth.contract(
        address=PSM_ADDRESS_BY_CHAIN[Chain.ETHEREUM],
        abi=MODULE_CORE_ABI,
    ),
    Chain.SEPOLIA: w3_sepolia.eth.contract(
        address=PSM_ADDRESS_BY_CHAIN[Chain.SEPOLIA],
        abi=MODULE_CORE_ABI,
    ),
}

PSM_USDE_START_BLOCK_BY_CHAIN = {
    Chain.ETHEREUM: 237528674,
    Chain.SEPOLIA: 237528674,
}
