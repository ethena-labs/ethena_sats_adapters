from web3 import Web3

from constants.chains import Chain
from constants.integration_token import Token

CHAIN_TO_CONFIG_MAP = {
    Chain.ETHEREUM: {
        "data_manager_api_origin": "https://data-manager-api.termmax.ts.finance",
        "chain_id": "1",
        "token_to_config_map": {
            Token.SUSDE: {
                "address": Web3.to_checksum_address(
                    "0x9d39a5de30e57443bff2a8307a4256c8797a3497"
                ),
                "start_block": 22678822,
            },
        },
    },
}
# NOTE: market deploy tx https://etherscan.io/tx/0xc26c8ebf4ece31273475024f644d5337f13244018e096a4054925a12a909f75b
