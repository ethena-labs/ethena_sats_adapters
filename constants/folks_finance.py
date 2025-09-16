import json
from utils.web3_utils import w3_avalanche
from enum import Enum
from constants.integration_token import Token

with open("abi/folks_finance_loan_manager.json") as loan_manager_abi_file:
    LOAN_MANAGER_ABI = json.load(loan_manager_abi_file)

LOAN_MANAGER_ADDRESS = w3_avalanche.to_checksum_address(
    "0xF4c542518320F09943C35Db6773b2f9FeB2F847e"
)
LOAN_MANAGER_CONTRACT = w3_avalanche.eth.contract(
    address=LOAN_MANAGER_ADDRESS,
    abi=LOAN_MANAGER_ABI,
)

TOKEN_TO_POOL_IDS = {Token.USDE: 55, Token.SUSDE: 56}
STARTING_BLOCKS = {Token.USDE: 68784025, Token.SUSDE: 68784034}

LOAN_TO_ADDRESSES_INDEXER_URL = (
    "https://indexer.xapp.folks.finance/partner/ethena/loans"
)
