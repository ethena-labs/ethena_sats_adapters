"""
Constants for Meridian Liquidity Provider
"""

from web3 import Web3

from constants.chains import Chain

PAGINATION_SIZE = 1999

# Meridian Liquidity Provider USDe Vault
MERIDIAN_LP_VAULT_CHAIN = Chain.ROBINHOOD
MERIDIAN_LP_VAULT_ADDRESS = Web3.to_checksum_address(
    "0x24b84023c8e4Da635be228C380C09bfE5271BF9d"
)
MERIDIAN_LP_VAULT_START_BLOCK = 22051004  # vault deployment block
