from dataclasses import dataclass

GET_USERS_API_URL = "https://protocol-service-api.tempestfinance.xyz/api/v1/users"
CHAIN_ID_SWELL = "1923"

ABI_FILENAME = "abi/tempest_symmetric_vault.json"

@dataclass
class VaultConfig:
    address: str
    genesis_block: int

VAULTS = [
  VaultConfig(address="0x1783eb6b8966f7a2c3aa9b913dd53353b2c8c873", genesis_block=965288)
]
