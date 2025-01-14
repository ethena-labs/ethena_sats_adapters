import os
import json
from dotenv import load_dotenv
from utils.web3_utils import (
    w3_arb,
)

from constants.ramses import RAMSES_NFP_MANAGER_ADDRESS, RAMSES_POOL_ADDRESS

with open("abi/ramses_nfp_manager.json") as f:
    nfp_manager_abi = json.load(f)

with open("abi/ramses_pool.json") as f:
    pool_abi = json.load(f)


nfp_manager = w3_arb.eth.contract(
    address=w3_arb.to_checksum_address(RAMSES_NFP_MANAGER_ADDRESS),
    abi=nfp_manager_abi,
)

pool = w3_arb.eth.contract(
    address=w3_arb.to_checksum_address(RAMSES_POOL_ADDRESS), abi=pool_abi
)
