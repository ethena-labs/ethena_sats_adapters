import os
import json
from dotenv import load_dotenv
from utils.web3_utils import (
    w3_arb,
)

from constants.ramses import RAMSES_GAUGE_ADDRESS, RAMSES_POOL_ADDRESS

with open("abi/ramses_gauge.json") as f:
    gauge_abi = json.load(f)

with open("abi/ramses_legacy_pool.json") as f:
    pool_abi = json.load(f)


gauge = w3_arb.eth.contract(
    address=RAMSES_GAUGE_ADDRESS, abi=gauge_abi
)

pool = w3_arb.eth.contract(
    address=RAMSES_POOL_ADDRESS, abi=pool_abi
)

