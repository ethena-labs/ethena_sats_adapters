import json
from utils.web3_utils import W3_BY_CHAIN, fetch_events_logs_with_retry, call_with_retry

from constants.chains import Chain
from constants.balancer import AURA_VOTER_PROXY


with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)

PAGE_SIZE = 1900


def get_user_balance(chain: Chain, user: str, token_address: str, block: int) -> float:
    w3 = W3_BY_CHAIN[chain]["w3"]

    token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)

    user_balance = call_with_retry(
        token_contract.functions.balanceOf(user),
        block,
    )

    return user_balance


def get_token_supply(chain: Chain, token_address: str, block: int) -> float:
    w3 = W3_BY_CHAIN[chain]["w3"]

    token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)

    token_supply = call_with_retry(
        token_contract.functions.totalSupply(),
        block,
    )

    return token_supply


def get_token_holders(chain: Chain, token_address: str, start_block: int) -> list:
    w3 = W3_BY_CHAIN[chain]["w3"]

    token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)

    token_holders = set()
    latest_block = w3.eth.get_block_number()

    while start_block < latest_block:
        to_block = min(start_block + PAGE_SIZE, latest_block)
        transfers = fetch_events_logs_with_retry(
            f"Getting Balancer Staked BPT Holders {token_address}",
            token_contract.events.Transfer(),
            start_block,
            to_block,
        )

        print(start_block, to_block, len(transfers), "Getting Balancer ERC20 Transfers")

        for transfer in transfers:
            if transfer["args"]["to"] != AURA_VOTER_PROXY[chain]:
                token_holders.add(transfer["args"]["to"])

        start_block += PAGE_SIZE

    return list(token_holders)
