import json

HYPERDRIVE_REGISTRY = "0xbe082293b646cb619a638d29e8eff7cf2f46aa3a"

HYPERDRIVE_ABI = None
with open("abi/IHyperdrive.json") as f:
    HYPERDRIVE_ABI = json.load(f)

HYPERDRIVE_MORPHO_ABI = None
with open("abi/IHyperdriveMorpho.json") as f:
    HYPERDRIVE_MORPHO_ABI = json.load(f)

HYPERDRIVE_REGISTRY_ABI = None
with open("abi/hyperdrive_registry.json") as f:
    HYPERDRIVE_REGISTRY_ABI = json.load(f)

MORPHO_ABI = None
with open("abi/IMorpho.json") as f:
    MORPHO_ABI = json.load(f)

ERC20_ABI = None
with open("abi/ERC20_abi.json") as f:
    ERC20_ABI = json.load(f)
