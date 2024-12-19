from dataclasses import dataclass

GET_USERS_API_URL = "https://protocol-service-api.tempestdev.xyz/api/v1/users"
CHAIN_ID_SWELL = "534352"

ABI_FILENAME = "abi/tempest_symmetric_vault.json"

@dataclass
class VaultConfig:
    address: str
    genesis_block: int

VAULTS = [
  VaultConfig(address="0x9674d655bf1a456c441157a5e8c5fa4c144e21e8", genesis_block=10717843)
]
