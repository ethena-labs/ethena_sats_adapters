
# USDe - cmETH 0.25%: https://agni.finance/info/v3/pairs/0x95d39c45668d59141dc5bcc940e6c191f1ebb98c

# USDT - USDe  0.01%: https://agni.finance/info/v3/pairs/0x36a7aff497eef6a9cd7d0e7bc243793fcb3e57e2

# sUSDe - USDe 0.05%: https://agni.finance/info/v3/pairs/0x07277f7c1567b5324aa50a3d2f1f003e2287fbfc

# USDC - USDe 0.01%: https://agni.finance/info/v3/pairs/0xbcf99c834e65e8a58090e20edc058279317865bd

from web3 import Web3
from eth_abi import encode
from eth_account.messages import encode_defunct
from eth_utils import keccak, to_bytes, to_hex


import json
from utils.web3_utils import (
    w3_mantle,
)


MAX_TICK_RANGE=887272
START_BLOCK=72629606

usde_cmeth_025 = Web3.to_checksum_address("0x95D39c45668D59141dc5bCC940e6C191f1ebB98c")
usde_usdt_001 = Web3.to_checksum_address("0x36A7aff497eeF6a9cd7d0e7bc243793fcb3E57E2")
susde_usde_005 = Web3.to_checksum_address("0x07277F7c1567b5324aA50a3d2F1F003E2287fBfc")
usdc_usde_001 = Web3.to_checksum_address("0xBCf99c834E65E8a58090E20eDc058279317865BD")
agni_position_manager = Web3.to_checksum_address("0x218bf598D1453383e2F4AA7b14fFB9BfB102D637")
usde_address = Web3.to_checksum_address('0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34')




with open("abi/agni_pool.json") as j:
    pool_abi = json.load(j)

with open("abi/agni_position_manager.json") as j:
    position_abi = json.load(j)


usde_cmeth_025_contract = w3_mantle.eth.contract(address=usde_cmeth_025, abi=pool_abi)
usde_usdt_001_contract = w3_mantle.eth.contract(address=usde_usdt_001, abi=pool_abi)
susde_usde_005_contract = w3_mantle.eth.contract(address=susde_usde_005, abi=pool_abi)
usdc_usde_001_contract = w3_mantle.eth.contract(address=usdc_usde_001, abi=pool_abi)
position_manager_contract = w3_mantle.eth.contract(address=agni_position_manager, abi=position_abi)




def compute_pool_address(token_a, token_b, fee):

    if token_a < token_b:
        token0, token1 = token_a, token_b
    else:
        token0, token1 = token_b, token_a

    pool_init_code_hash = "0xaf9bd540c3449b723624376f906d8d3a0e6441ff18b847f05f4f85789ab64d9a"
    agni_pool_deployer = "0xe9827B4EBeB9AE41FC57efDdDd79EDddC2EA4d03"

    encoded_params = encode(
        ['address', 'address', 'uint24'],
        [token0, token1, fee],
    )

    salt = to_hex(keccak(encoded_params))

    return get_create2_address(
        agni_pool_deployer,
        salt,
        pool_init_code_hash,
    )


def get_create2_address(deployer_address, salt, init_code_hash):
    deployer_address_bytes = to_bytes(hexstr=deployer_address)
    salt_bytes = to_bytes(hexstr=salt)
    init_code_hash_bytes = to_bytes(hexstr=init_code_hash)

    return Web3.to_checksum_address(
        keccak(b'\xff' + deployer_address_bytes + salt_bytes + init_code_hash_bytes)[12:].hex()
    )


if __name__ == '__main__':
    print(compute_pool_address('0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34', '0xE6829d9a7eE3040e1276Fa75293Bde931859e8fA', 2500))