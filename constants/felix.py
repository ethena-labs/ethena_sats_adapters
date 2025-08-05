import json
from utils.web3_utils import W3_BY_CHAIN
from constants.chains import Chain
from web3 import Web3

# Load the ERC4626 ABI from the correct path
with open("abi/felix_usde.json") as f:
    felix_usde_abi = json.load(f)

# Set the Felix USDe Vault address and contract
FELIX_USDE_VAULT_ADDRESS = Web3.to_checksum_address("0x835FEBF893c6DdDee5CF762B0f8e31C5B06938ab")
FELIX_USDE_VAULT_CONTRACT = W3_BY_CHAIN[Chain.HYPEREVM]["w3"].eth.contract(
    address=FELIX_USDE_VAULT_ADDRESS,
    abi=felix_usde_abi,
)

# Set the Felix USDe holders subgraph URL
FELIX_USDE_HOLDERS_GRAPH_URL = "https://api.goldsky.com/api/public/project_cmdod1b8ua1yt01ukdmucfj2c/subgraphs/felix-usde/1.0.5/gn"
