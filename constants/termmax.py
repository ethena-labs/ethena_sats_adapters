from web3 import Web3

from constants.chains import Chain
from constants.integration_token import Token

CHAIN_TO_CONFIG_MAP = {
    Chain.ETHEREUM: {
        "data_manager_api_origin": "https://data-manager-api.termmax.ts.finance",
        "chain_id": "1",
        "token_to_address_map": {
            Token.USDE: Web3.to_checksum_address(
                "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"
            ),
            Token.SUSDE: Web3.to_checksum_address(
                "0x9d39a5de30e57443bff2a8307a4256c8797a3497"
            ),
        },
    },
}

TERMMAX_SUSDE_START_BLOCK = 3376668
TERMMAX_USDE_START_BLOCK = 3376668
