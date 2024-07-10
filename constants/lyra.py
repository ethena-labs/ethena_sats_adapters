import json
from typing import TypedDict, Dict
from utils.web3_utils import W3_BY_CHAIN
from web3.contract.contract import Contract
from constants.chains import Chain
from constants.integration_ids import IntegrationID

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


class LyraVaultDetails(TypedDict):
    start: int
    chain: str
    integration_token: Contract
    bridge: Contract
    vault_token: Contract
    page_size: int


# NOTE: does not handle cross-chain transfers of vault tokens
LYRA_CONTRACTS_AND_START_BY_TOKEN: Dict[IntegrationID, LyraVaultDetails] = {
    IntegrationID.LYRA_SUSDE_BULL_MAINNET: LyraVaultDetails(
        start=20211445,
        chain=Chain.ETHEREUM,
        integration_token=W3_BY_CHAIN["eth"].eth.contract(
            address="0x9d39a5de30e57443bff2a8307a4256c8797a3497", abi=erc20_abi
        ),  # sUSDe
        bridge=W3_BY_CHAIN["eth"].eth.contract(address="0xE3E96892D30E0ee1a8131BAf87c891201F7137bf", abi=erc20_abi),
        vault_token=W3_BY_CHAIN["eth"].eth.contract(
            address="0x1d080C689B930f9dEa69CB3B4Bc6b8c213DFC2ad", abi=erc20_abi
        ),
        page_size=1000,
    ),
    IntegrationID.LYRA_SUSDE_BULL_MAINNET: LyraVaultDetails(
        start=227626020,
        chain=Chain.ARBITRUM,
        integration_token=W3_BY_CHAIN["arb"].eth.contract(
            address="0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2", abi=erc20_abi
        ),  # sUSDe
        bridge=W3_BY_CHAIN["arb"].eth.contract(address="0x3c143EA5eBaB50ad6D2B2d14FA719234d1d38F1b", abi=erc20_abi),
        vault_token=W3_BY_CHAIN["arb"].eth.contract(
            address="0x81494d722DDceDbA31ac40F28daFa66b207f232B", abi=erc20_abi
        ),
        page_size=5000,
    ),
}
