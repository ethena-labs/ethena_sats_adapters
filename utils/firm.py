import json
from typing import Any, Set
from web3 import Web3
from utils.web3_utils import (
    call_with_retry,
    fetch_events_logs_with_retry,
    w3,
)

from constants.firm import SUSDE_MARKET_ADDRESS

with open("abi/firm_market.json") as f:
    firm_market_abi = json.load(f)

with open("abi/firm_simple_escrow.json") as f:
    firm_simple_escrow_abi = json.load(f)

with open("abi/curve_stable_swap_ng_lp.json") as f:
    curve_stable_swap_ng_lp_abi = json.load(f)

with open("abi/yearn_v2_vault.json") as f:
    yearn_v2_vault_abi = json.load(f)

def get_firm_market_contract(marketAddress: str):
    return w3.eth.contract(
        address=Web3.to_checksum_address(marketAddress), abi=firm_market_abi
    )

def get_escrow_contract(user_address: str, marketAddress: str):
    escrow_address: str = get_firm_market_contract(marketAddress).functions.escrows(
        user_address
    ).call()
    return w3.eth.contract(
        address=Web3.to_checksum_address(escrow_address), abi=firm_simple_escrow_abi
    )

def get_curve_lp_contract(lpAddress: str):
    return w3.eth.contract(
        address=Web3.to_checksum_address(lpAddress), abi=curve_stable_swap_ng_lp_abi
    )

def get_yearn_vault_v2_contract(yvAddress: str):
    return w3.eth.contract(
        address=Web3.to_checksum_address(yvAddress), abi=yearn_v2_vault_abi
    )

def get_firm_user_balance(user: str, marketAddress: str, block: int) -> Any:
        # get user escrow
        escrow_contract = get_escrow_contract(user, marketAddress)
        # get the balance from the escrow
        balance = call_with_retry(
            escrow_contract.functions.balance(),
            block,
        )
        return balance

def get_firm_market_participants(
        start_block: int,
        marketAddress: str,
    ) -> Set[str]:
        page_size = 1900
        target_block = w3.eth.get_block_number()

        firm_market_contract = get_firm_market_contract(marketAddress)

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            escrow_creations = fetch_events_logs_with_retry(
                f"Inverse Finance FiRM users from {start_block} to {to_block}",
                firm_market_contract.events.CreateEscrow(),
                start_block,
                to_block,
            )
            for escrow_creation in escrow_creations:
                all_users.add(escrow_creation["args"]["user"])
            start_block += page_size
        return all_users