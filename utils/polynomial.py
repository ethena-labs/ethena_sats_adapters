import os
import json
from dotenv import load_dotenv
from utils.web3_utils import (
    w3_polynomial,
)

from constants.polynomial import POLYNOMIAL_CORE_ACCOUNT_ADDRESS, POLYNOMIAL_CORE_PROXY_ADDRESS
with open("abi/polynomial_core_proxy.json") as f:
    core_proxy_abi = json.load(f)

with open("abi/polynomial_core_account.json") as f:
    core_account_proxy_abi = json.load(f)


core_proxy_contract = w3_polynomial.eth.contract(
    address=POLYNOMIAL_CORE_PROXY_ADDRESS, abi=core_proxy_abi
)

core_account_proxy_contract = w3_polynomial.eth.contract(
    address=POLYNOMIAL_CORE_ACCOUNT_ADDRESS, abi=core_account_proxy_abi
)