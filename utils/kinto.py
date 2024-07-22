from web3 import Web3
from web3.contract import Contract
import json

from constants.kinto import KINTO_USDE_ADDRESS, KINTO_SUSDE_ADDRESS, KINTO_ENA_ADDRESS
from utils.web3_utils import fetch_events_logs_with_retry

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)
    
def get_contract(web3: Web3, address: str) -> Contract:
    return web3.eth.contract(address=address, abi=erc20_abi)

def get_kinto_usde_contract(web3: Web3) -> Contract:
    return get_contract(web3, KINTO_USDE_ADDRESS)

def get_kinto_susde_contract(web3: Web3) -> Contract:
    return get_contract(web3, KINTO_SUSDE_ADDRESS)

def get_kinto_ena_contract(web3: Web3) -> Contract:
    return get_contract(web3, KINTO_ENA_ADDRESS)

def fetch_participants(contract: Contract, from_block: int) -> list:
    transfer_event = contract.events.Transfer()
    logs = fetch_events_logs_with_retry(
        label="Transfer Events",
        contract_event=transfer_event,
        from_block=from_block,
        to_block="latest"
    )

    participants = set()
    for log in logs:
        participants.add(log['args']['from'])
        participants.add(log['args']['to'])

    return list(participants)
