import os
from web3 import Web3

# TODO: this needs to be updated to the actual market when ready - 
# this is a placeholder (Hyperithm WildcatFast USD Coin) for integration testing
WILDCAT_MARKET_ADDRESS = Web3.to_checksum_address(os.getenv("WILDCAT_MARKET_ADDRESS", "0x9e597911a484713f12f6efc29c49bebc64fa2144"))


WILDCAT_SUBGRAPH_URL = os.getenv(
    "WILDCAT_SUBGRAPH_URL",
    "https://subgraph.satsuma-prod.com/db4945988e6f/dillons-team--345508/mainnet/version/v2.0.19/api",
)
