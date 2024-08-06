import json
from utils.web3_utils import (
    w3_fraxtal,
    fetch_events_logs_with_retry,
    call_with_retry,
)

from constants.balancer import BALANCER_FRAXTAL_DEPLOYMENT_BLOCK


with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)

PAGE_SIZE = 1900


def fetch_participants(token):
    token_contract = w3_fraxtal.eth.contract(address=token, abi=erc20_abi)

    participants = set()
    start_block = BALANCER_FRAXTAL_DEPLOYMENT_BLOCK
    latest_block = w3_fraxtal.eth.get_block_number()
    while start_block < latest_block:
        to_block = min(BALANCER_FRAXTAL_DEPLOYMENT_BLOCK + PAGE_SIZE, latest_block)
        transfers = fetch_events_logs_with_retry(
            f"Getting Balancer v2 participants {token}",
            token_contract.events.Transfer(),
            start_block,
            to_block,
        )

        print(start_block, to_block, len(transfers), "Getting Balancer Gauge Transfers")

        for transfer in transfers:
            participants.add(transfer["args"]["to"])

        start_block += PAGE_SIZE

    return participants
