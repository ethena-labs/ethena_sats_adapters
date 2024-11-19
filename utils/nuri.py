import json
from utils.web3_utils import (
    w3_scroll,
)

from constants.nuri import NURI_NFP_MANAGER_ADDRESS, NURI_POOL_ADDRESS

with open("abi/nuri_nfp_manager.json") as f:
    nfp_manager_abi = json.load(f)

with open("abi/nuri_pool.json") as f:
    pool_abi = json.load(f)


nfp_manager = w3_scroll.eth.contract(
    address=NURI_NFP_MANAGER_ADDRESS, abi=nfp_manager_abi
)

pool = w3_scroll.eth.contract(address=NURI_POOL_ADDRESS, abi=pool_abi)
