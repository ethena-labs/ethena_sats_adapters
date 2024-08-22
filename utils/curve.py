import json
from utils.web3_utils import w3 as w3_eth

import constants.curve as curve_constants


with open("abi/curve_llamalend_controller.json") as f:
    curve_llamalend_controller_abi = json.load(f)

with open("abi/curve_llamalend_amm.json") as f:
    curve_llamalend_amm_abi = json.load(f)
    

# Llamalend contracts:

# SUSDe
curve_llamalend_susde_controller_contract = w3_eth.eth.contract(
    address=curve_constants.CURVE_LLAMALEND_ETHEREUM_SUSDE_CONTROLLER, 
    abi=curve_llamalend_controller_abi
)
curve_llamalend_susde_amm_contract = w3_eth.eth.contract(
    address=curve_constants.CURVE_LLAMALEND_ETHEREUM_SUSDE_AMM, 
    abi=curve_llamalend_amm_abi
)

# USDe
curve_llamalend_susde_controller_contract = w3_eth.eth.contract(
    address=curve_constants.CURVE_LLAMALEND_ETHEREUM_USDE_CONTROLLER, 
    abi=curve_llamalend_controller_abi
)
curve_llamalend_susde_amm_contract = w3_eth.eth.contract(
    address=curve_constants.CURVE_LLAMALEND_ETHEREUM_USDE_AMM, 
    abi=curve_llamalend_amm_abi
)
