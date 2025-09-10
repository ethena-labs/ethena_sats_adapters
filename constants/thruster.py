import json
from web3 import Web3
from web3.contract import Contract
from utils.web3_utils import w3_blast

MAX_TICK_RANGE = 7000

THRUSTER_USDE_POOL_ADDRESS = Web3.to_checksum_address(
    "0x8C1bb76510D6873a4A156A9Cb394E74A3783BDB5"
)

THRUSTER_NFP_ADDRESS = Web3.to_checksum_address(
    "0x434575EaEa081b735C985FA9bf63CD7b87e227F9"
)

HYPERLOCK_DEPOSIT_ADDRESS = Web3.to_checksum_address(
    "0xc28EffdfEF75448243c1d9bA972b97e32dF60d06"
)

JUICE_USDE_VAULT_ADDR = Web3.to_checksum_address(
    "0xc1B1aE2502D2cDEF4772FB4A4a6fcBf4fd9c1b80"
)

PARTICLE_LEVERAGED_POOL_ADDRESS = Web3.to_checksum_address(
    "0x121B5ac4De4a3E6F4171956BC26ceda40Cb61a56"
)

JUICE_TOKEN_ID = 111969


THRUSTER_NFP_ABI = json.load(open("abi/thruster_nfp.json"))
THRUSTER_POOL_ABI = json.load(open("abi/thruster_pool.json"))

thruster_nfp_contract: Contract = w3_blast.eth.contract(
    address=THRUSTER_NFP_ADDRESS, abi=THRUSTER_NFP_ABI
)

thruster_usde_pool_contract: Contract = w3_blast.eth.contract(
    address=THRUSTER_USDE_POOL_ADDRESS, abi=THRUSTER_POOL_ABI
)
