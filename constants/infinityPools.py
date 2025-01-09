
# USDC-sUSDe
from web3 import Web3


import json
from utils.web3_utils import (
    w3_base,
)


START_BLOCK = 24224743
# Maximum range of blocks RPC can handle to fetch the events from in one call
MAX_BLOCKS_IN_ONE_CALL = 20_000


usdc_sUSDe_15 = Web3.to_checksum_address(
    "0x8c14ad2b5365eb93a31b8dd75dfb203a1a40264b")
sUSDe_address = Web3.to_checksum_address(
    "0x55255F4d6a23208659Ba09589d6ac1bb6A9e9ada"
)

infinityPools_factory = Web3.to_checksum_address(
    "0xE3795b74B53971A418F4B6Ef67dB054Ed482Afef")
infinityPools_periphery = Web3.to_checksum_address(
    "0x31d85244058d635ea206f007e51a7f61ccb9d53c")


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
    address=usdc_sUSDe_15, abi=infinityPool_abi)


def get_pool_address(token_a, token_b, splits):
    return infinityPools_factory_contract.functions.getPool(token_a, token_b, splits).call()


# get position type, pool address and lpOrSwapper number given tokenId
def decode_id(id: int):
    enum_value = (id >> 248) & 0xFF
    pool_address = (id >> 88) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    lp_or_swapper_number = id & ((1 << 88) - 1)
    return enum_value, f"0x{pool_address:040x}", lp_or_swapper_number


if __name__ == '__main__':
    print(get_pool_address(Web3.to_checksum_address('0x55255f4d6a23208659ba09589d6ac1bb6a9e9ada'),
          Web3.to_checksum_address('0xfcc8e983068f88e8af71b8471135043fedad8460'), 15))
