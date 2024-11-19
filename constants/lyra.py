import json
from typing import TypedDict, Dict
from utils.web3_utils import W3_BY_CHAIN
from web3.contract.contract import Contract
from web3 import Web3
from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from enum import Enum

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


class DetailType(Enum):
    Vault = "Vault"
    Exchange = "Exchange"


class LyraVaultDetails(TypedDict):
    detail_type: DetailType
    start: int
    chain: str
    page_size: int
    integration_token: Contract | None
    bridge: Contract | None
    vault_token: Contract | None


# NOTE: does not handle cross-chain transfers of vault tokens
LYRA_CONTRACTS_AND_START_BY_TOKEN: Dict[IntegrationID, LyraVaultDetails] = {
    IntegrationID.LYRA_SUSDE_BULL_MAINNET: LyraVaultDetails(
        detail_type=DetailType.Vault,
        start=20211445,
        chain=Chain.ETHEREUM,
        integration_token=W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.contract(
            address=Web3.to_checksum_address(
                "0x9d39a5de30e57443bff2a8307a4256c8797a3497"
            ),
            abi=erc20_abi,
        ),  # sUSDe
        bridge=W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.contract(
            address=Web3.to_checksum_address(
                "0xE3E96892D30E0ee1a8131BAf87c891201F7137bf"
            ),
            abi=erc20_abi,
        ),
        vault_token=W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.contract(
            address=Web3.to_checksum_address(
                "0x1d080C689B930f9dEa69CB3B4Bc6b8c213DFC2ad"
            ),
            abi=erc20_abi,
        ),
        page_size=5000,
    ),
    IntegrationID.LYRA_SUSDE_BULL_ARBITRUM: LyraVaultDetails(
        detail_type=DetailType.Vault,
        start=227626020,
        chain=Chain.ARBITRUM,
        integration_token=W3_BY_CHAIN[Chain.ARBITRUM]["w3"].eth.contract(
            address=Web3.to_checksum_address(
                "0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2"
            ),
            abi=erc20_abi,
        ),  # sUSDe
        bridge=W3_BY_CHAIN[Chain.ARBITRUM]["w3"].eth.contract(
            address=Web3.to_checksum_address(
                "0x3c143EA5eBaB50ad6D2B2d14FA719234d1d38F1b"
            ),
            abi=erc20_abi,
        ),
        vault_token=W3_BY_CHAIN[Chain.ARBITRUM]["w3"].eth.contract(
            address=Web3.to_checksum_address(
                "0x81494d722DDceDbA31ac40F28daFa66b207f232B"
            ),
            abi=erc20_abi,
        ),
        page_size=20000,
    ),
    IntegrationID.LYRA_SUSDE_EXCHANGE_DEPOSIT: LyraVaultDetails(
        detail_type=DetailType.Exchange,
        start=11481048,
        chain=Chain.Lyra,
        page_size=20000,
    ),
}
