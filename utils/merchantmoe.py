import json
from pathlib import Path

from dotenv import load_dotenv

from constants.merchantmoe import MERCHANT_MOE_LIQUIDITY_HELPER_CONTRACT, METH_USDE_MERCHANT_MOE_LBT_CONTRACT
from utils.web3_utils import w3_mantle

load_dotenv()

merchant_moe_lb_pair_abi = json.load(
    open(Path(__file__).parent.parent / "abi/merchant_moe_lb_pair.json")
)

merchant_moe_liquidity_helper_abi = json.load(
    open(Path(__file__).parent.parent / "abi/merchant_moe_liquidity_helper.json")
)

lb_pair_contract = w3_mantle.eth.contract(address=METH_USDE_MERCHANT_MOE_LBT_CONTRACT, abi=merchant_moe_lb_pair_abi)
liquidity_helper_contract = w3_mantle.eth.contract(address=MERCHANT_MOE_LIQUIDITY_HELPER_CONTRACT, abi=merchant_moe_liquidity_helper_abi)