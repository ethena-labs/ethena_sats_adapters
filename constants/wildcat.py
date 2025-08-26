import os
from web3 import Web3

WILDCAT_MARKET_ADDRESS = Web3.to_checksum_address(os.getenv("WILDCAT_MARKET_ADDRESS", "0x9Fa4b300c474B86ffaA44288d2496Ba1b735f9FD"))

WILDCAT_SUBGRAPH_URL = os.getenv(
    "WILDCAT_SUBGRAPH_URL",
    "https://subgraph.satsuma-prod.com/db4945988e6f/dillons-team--345508/mainnet/version/v2.0.19/api",
)
