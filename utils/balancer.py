import json
from web3 import Web3

from constants.chains import Chain
from constants.balancer import AURA_VOTER_PROXY, BALANCER_VAULT
from utils.web3_utils import W3_BY_CHAIN, fetch_events_logs_with_retry, call_with_retry


with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)

with open("abi/balancer_vault.json") as f:
    vault_abi = json.load(f)

with open("abi/balancer_csp.json") as f:
    composable_abi = json.load(f)

PAGE_SIZE = 1900

ZERO_ADRESS = "0x0000000000000000000000000000000000000000"


def get_vault_pool_token_balance(
    chain: Chain, pool_id: str, token_address: str, block: int | str
) -> float:
    w3 = W3_BY_CHAIN[chain]["w3"]

    vaut_contract = w3.eth.contract(
        address=w3.to_checksum_address(BALANCER_VAULT), abi=vault_abi
    )

    tokens, balances, _ = call_with_retry(
        vaut_contract.functions.getPoolTokens(pool_id),
        block,
    )

    try:
        token_index = tokens.index(token_address)
        return balances[token_index]
    except ValueError:
        raise ValueError(f"Token {token_address} not found in the Pool {pool_id}")


def get_user_balance(
    chain: Chain, user: str, token_address: str, block: int | str
) -> float:
    w3 = W3_BY_CHAIN[chain]["w3"]

    token_contract = w3.eth.contract(
        address=w3.to_checksum_address(token_address), abi=erc20_abi
    )

    user_balance = call_with_retry(
        token_contract.functions.balanceOf(user),
        block,
    )

    return user_balance


def get_bpt_supply(
    chain: Chain, bpt_address: str, has_preminted_bpts: bool, block: int | str
) -> float:
    w3 = W3_BY_CHAIN[chain]["w3"]

    if has_preminted_bpts:
        bpt_contract = w3.eth.contract(
            address=Web3.to_checksum_address(bpt_address), abi=composable_abi
        )

        bpt_supply = call_with_retry(
            bpt_contract.functions.getActualSupply(),
            block,
        )
    else:
        bpt_contract = w3.eth.contract(
            address=Web3.to_checksum_address(bpt_address), abi=erc20_abi
        )

        bpt_supply = call_with_retry(
            bpt_contract.functions.totalSupply(),
            block,
        )

    return bpt_supply


def get_potential_token_holders(
    chain: Chain, token_address: str, start_block: int
) -> list:
    w3 = W3_BY_CHAIN[chain]["w3"]

    token_contract = w3.eth.contract(
        address=Web3.to_checksum_address(token_address), abi=erc20_abi
    )

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
            if transfer["args"]["to"] not in [AURA_VOTER_PROXY[chain], ZERO_ADRESS]:
                token_holders.add(transfer["args"]["to"])

        start_block += PAGE_SIZE

    return list(token_holders)
