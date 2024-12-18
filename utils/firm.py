import json
from web3 import Web3
from utils.web3_utils import (
    w3,
)

from constants.firm import SUSDE_MARKET_ADDRESS

with open("abi/firm_market.json") as f:
    firm_market_abi = json.load(f)

with open("abi/firm_simple_escrow.json") as f:
    firm_simple_escrow_abi = json.load(f)


firm_susde_market_contract = w3.eth.contract(
    address=SUSDE_MARKET_ADDRESS, abi=firm_market_abi
)


def get_escrow_contract(user_address: str):
    escrow_address: str = firm_susde_market_contract.functions.escrows(
        user_address
    ).call()
    return w3.eth.contract(
        address=Web3.to_checksum_address(escrow_address), abi=firm_simple_escrow_abi
    )
