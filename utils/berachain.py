from constants.berachain import ZERO_ADRESS
from constants.chains import Chain
from utils.web3_utils import W3_BY_CHAIN, call_with_retry, fetch_events_logs_with_retry
from web3 import Web3

import json

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)

PAGE_SIZE = 2000

BERACHAIN_W3 = W3_BY_CHAIN[Chain.BERACHAIN]["w3"]

def get_pool_token_holders(
    token_address: str, reward_vault: str, start_block: int
) -> list:

    token_contract = BERACHAIN_W3.eth.contract(
        address=Web3.to_checksum_address(token_address), abi=erc20_abi
    )

    token_holders = set()
    latest_block = BERACHAIN_W3.eth.get_block_number()

    print(latest_block)

    while start_block < latest_block:
        to_block = min(start_block + PAGE_SIZE, latest_block)
        transfers = fetch_events_logs_with_retry(
            f"Getting Berachain Pool Token Holder {token_address}",
            token_contract.events.Transfer(),
            start_block,
            to_block,
        )

        print(start_block, to_block, len(transfers), "Getting Balancer ERC20 Transfers")
        
        IGNORED_ADDRESSES = [ZERO_ADRESS]
        if reward_vault is not None:
            IGNORED_ADDRESSES.append(reward_vault)

        for transfer in transfers:
            if transfer["args"]["to"] not in IGNORED_ADDRESSES:
                token_holders.add(transfer["args"]["to"])

        start_block += PAGE_SIZE

    return list(token_holders)

def get_user_balance(
    user: str, token_address: str, block: int | str
) -> float:

    token_contract = BERACHAIN_W3.eth.contract(
        address=BERACHAIN_W3.to_checksum_address(token_address), abi=erc20_abi
    )

    user_balance = call_with_retry(
        token_contract.functions.balanceOf(user),
        block,
    )

    return user_balance