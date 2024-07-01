import os
import json
from dotenv import load_dotenv
from utils.web3_utils import (
    w3_arb,
)

from constants.synthetix import SYNTHETIX_ARB_CORE_PROXY_ADDRESS, SYNTHETIX_ARB_CORE_ACCOUNT_PROXY_ADDRESS

with open("abi/synthetix_core_proxy.json") as f:
    core_proxy_abi = json.load(f)

with open("abi/synthetix_core_account_proxy.json") as f:
    core_account_proxy_abi = json.load(f)


core_proxy_contract = w3_arb.eth.contract(
    address=SYNTHETIX_ARB_CORE_PROXY_ADDRESS, abi=core_proxy_abi
)

core_account_proxy_contract = w3_arb.eth.contract(
    address=SYNTHETIX_ARB_CORE_ACCOUNT_PROXY_ADDRESS, abi=core_account_proxy_abi
)
