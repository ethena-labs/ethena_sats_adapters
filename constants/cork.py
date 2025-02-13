import json
import pathlib
from enum import Enum
from collections import defaultdict
from web3 import Web3
from constants.chains import Chain
from utils.web3_utils import (
    w3,
    w3_sepolia,
)

class TokenType(Enum):
    RA = 1
    PA = 2

PAGINATION_SIZE = 2000

ZERO_ADDRESS = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")

ABI_PATH = pathlib.Path(__file__).parent.parent / "abi"
with open(ABI_PATH / "ERC20_abi.json") as f:
    ERC20_ABI = json.load(f)
with open(ABI_PATH / "cork" / "ModuleCore.json") as f:
    MODULE_CORE_ABI = json.load(f)
with open(ABI_PATH / "cork" / "ICorkHook.json") as f:
    ICORK_HOOK_ABI = json.load(f)

PSM_ADDRESS_BY_CHAIN = {
    Chain.ETHEREUM: Web3.to_checksum_address("0x0e1968D9f29E99f14F9023021219eCedD67EB712"),
    Chain.SEPOLIA: Web3.to_checksum_address("0xF6a5b7319DfBc84EB94872478be98462aA9Aab99"),
}

LV_ADDRESS_BY_CHAIN = PSM_ADDRESS_BY_CHAIN

AMM_ADDRESS_BY_CHAIN = {
    Chain.ETHEREUM: Web3.to_checksum_address("0x0f956f42d92e478e9d61b5432c5080c09134AA88"),
    Chain.SEPOLIA: Web3.to_checksum_address("0xf190c07670Db093962814393daCbF833CE02ea88"),
}

AMM_CONTRACT_BY_CHAIN = {
    Chain.ETHEREUM: w3.eth.contract(
        address=AMM_ADDRESS_BY_CHAIN[Chain.ETHEREUM],
        abi=ICORK_HOOK_ABI,
    ),
    Chain.SEPOLIA: w3_sepolia.eth.contract(
        address=AMM_ADDRESS_BY_CHAIN[Chain.SEPOLIA],
        abi=ICORK_HOOK_ABI,
    ),
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

# block height of first deployment of contract or pair
PSM_USDE_START_BLOCK_BY_CHAIN = {
    Chain.ETHEREUM: 21840338,
    Chain.SEPOLIA: 7214863,
}

# block height of first deployment of contract or pair
PSM_SUSDE_START_BLOCK_BY_CHAIN = {
    Chain.ETHEREUM: 21840338,
    Chain.SEPOLIA: 7214863,
}

# See: https://docs.ethena.fi/solution-design/key-addresses
# See: https://docs.ethena.fi/resources/testnet
USDE_TOKEN_ADDRESS_FOR_L2 = Web3.to_checksum_address("0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34")
USDE_TOKEN_ADDRESS_BY_CHAIN = defaultdict(lambda: USDE_TOKEN_ADDRESS_FOR_L2, {
    Chain.ETHEREUM: Web3.to_checksum_address("0x4c9EDD5852cd905f086C759E8383e09bff1E68B3"),
    Chain.SEPOLIA: Web3.to_checksum_address("0x9458caaca74249abbe9e964b3ce155b98ec88ef2"),
})

SUSDE_TOKEN_ADDRESS_FOR_L2 = Web3.to_checksum_address("0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2")
SUSDE_TOKEN_ADDRESS_BY_CHAIN = defaultdict(lambda: SUSDE_TOKEN_ADDRESS_FOR_L2, {
    Chain.ETHEREUM: Web3.to_checksum_address("0x9d39a5de30e57443bff2a8307a4256c8797a3497"),
})
