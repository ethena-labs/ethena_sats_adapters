import json
from enum import IntEnum

HYPERDRIVE_SUSDE_POOL_ADDRESS = "0x05b65FA90AD702e6Fd0C3Bd7c4c9C47BAB2BEa6b"
HYPERDRIVE_SUSDE_POOL_DEPLOYMENT_BLOCK = 20931644

HYPERDRIVE_MORPHO_ABI = None
with open("abi/IHyperdriveMorpho.json") as f:
    HYPERDRIVE_MORPHO_ABI = json.load(f)

ERC20_ABI = None
with open("abi/ERC20_abi.json") as f:
    ERC20_ABI = json.load(f)

class HyperdrivePrefix(IntEnum):
    r"""The asset ID is used to encode the trade type in a transaction receipt"""

    LP = 0
    LONG = 1
    SHORT = 2
    WITHDRAWAL_SHARE = 3
