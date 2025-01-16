
# USDC-sUSDe
from web3 import Web3


import json
from utils.web3_utils import (
    w3_base,
)


START_BLOCK = 24888600
# Maximum range of blocks RPC can handle to fetch the events from in one call
MAX_BLOCKS_IN_ONE_CALL = 20_000


usdc_sUSDe = Web3.to_checksum_address(
    "0x2175A80B99FF2e945CcCE92FD0365f0CB5C5E98D")
wstETH_sUSDe = Web3.to_checksum_address(
    "0xC3A51F01bc43b1a41B1a1ccaa64c0578cF40BA1F")
sUSDe_address = Web3.to_checksum_address(
    "0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2"
)

infinityPools_factory = Web3.to_checksum_address(
    "0x86342D7bBe93cB640A6c57d4781f04d93a695f08")
infinityPools_periphery = Web3.to_checksum_address(
    "0xF8FAD01B2902fF57460552C920233682c7c011a7")


with open("abi/infinityPool.json") as j:
    infinityPool_abi = json.load(j)

with open("abi/infinityPools_periphery.json") as j:
    infinityPools_periphery_abi = json.load(j)

with open("abi/infinityPools_factory.json") as j:
    infinityPools_factory_abi = json.load(j)


infinityPools_factory_contract = w3_base.eth.contract(
    address=infinityPools_factory, abi=infinityPools_factory_abi)
infinityPools_periphery_contract = w3_base.eth.contract(
    address=infinityPools_periphery, abi=infinityPools_periphery_abi)
infinityPool_contract = w3_base.eth.contract(
    address=usdc_sUSDe, abi=infinityPool_abi)


def get_pool_address(token_a, token_b, splits):
    return infinityPools_factory_contract.functions.getPool(token_a, token_b, splits).call()


# get position type, pool address and lpOrSwapper number given tokenId
def decode_id(id_to_decode: int):
    enum_value = (id_to_decode >> 248) & 0xFF
    pool_address = (id_to_decode >> 88) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    lp_or_swapper_number = id_to_decode & ((1 << 88) - 1)
    return enum_value, f"0x{pool_address:040x}", lp_or_swapper_number


if __name__ == '__main__':
    print(get_pool_address(Web3.to_checksum_address('0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2'),
          Web3.to_checksum_address('0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'), 17))
