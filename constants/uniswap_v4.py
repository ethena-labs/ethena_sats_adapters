import json
from web3 import Web3
from web3.contract import Contract
from utils.web3_utils import w3

UNISWAP_V4_USDE_POOL = Web3.to_bytes(
    hexstr="0x63bb22f47c7ede6578a25c873e77eb782ec8e4c19778e36ce64d37877b5bd1e7"
)

UNISWAP_V4_STATE_VIEW = Web3.to_checksum_address(
    "0x7fFE42C4a5DEeA5b0feC41C94C136Cf115597227"
)
UNISWAP_V4_POOL_MANAGER = Web3.to_checksum_address(
    "0x000000000004444c5dc75cB358380D2e3dE08A90"
)
UNISWAP_V4_NFPM_ADDRESS = Web3.to_checksum_address(
    "0xbD216513d74C8cf14cf4747E6AaA6420FF64ee9e"
)

UNISWAP_V4_SV_ABI = json.load(open("abi/uniswap_v4_sv.json"))
UNISWAP_V4_PM_ABI = json.load(open("abi/uniswap_v4_pm.json"))
UNISWAP_V4_NFPM_ABI = json.load(open("abi/uniswap_v4_nfpm.json"))

uniswap_v4_sv_contract: Contract = w3.eth.contract(
    address=UNISWAP_V4_STATE_VIEW, abi=UNISWAP_V4_SV_ABI
)
uniswap_v4_pm_contract: Contract = w3.eth.contract(
    address=UNISWAP_V4_POOL_MANAGER, abi=UNISWAP_V4_PM_ABI
)
uniswap_v4_nfpm_contract: Contract = w3.eth.contract(
    address=UNISWAP_V4_NFPM_ADDRESS, abi=UNISWAP_V4_NFPM_ABI
)
