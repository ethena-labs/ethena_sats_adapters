import json
from typing import TypedDict, Dict
from utils.web3_utils import W3_BY_CHAIN
from web3.contract.contract import Contract

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


class LyraVaultDetails(TypedDict):
    start: int
    chain: str
    bridge: str
    vault_token: Contract


SUSDE_MAINNET_TOKEN_ADDRESS = "0x0000000"

SUSDE_CONTRACT = W3_BY_CHAIN["eth"].eth.contract(address="0x000000000000000000000000", abi=erc20_abi)


LYRA_CONTRACTS_AND_START_BY_TOKEN: Dict[str, LyraVaultDetails] = {
    "SUSDE_LONGPP_MAINNET": LyraVaultDetails(
        start=00000,
        chain="eth",
        bridge_address="0x000000000000000000",
        vault_token=W3_BY_CHAIN["eth"].eth.contract(address="0x000000000000000000000000", abi=erc20_abi),
    )
}
