from web3 import Web3

from constants.chains import Chain
from constants.integration_token import Token

CHAIN_TO_CONFIG_MAP = {
    Chain.ETHEREUM: {
        "data_manager_api_origin": "https://data-manager-api.termmax.ts.finance",
        "chain_id": "1",
        "token_to_config_map": {
            Token.PT_SUSDE_25SEP2025: {
                "address": Web3.to_checksum_address(
                    "0x9F56094C450763769BA0EA9Fe2876070c0fD5F77"
                ),
                "start_block": 22886966, # market deploy tx: https://etherscan.io/tx/0x129ce6a2e3bed607e9b70613c2fa45217adfb87d8da83397a670a360606bbf62
            },
        },
    },
}
