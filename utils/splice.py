import json
import logging

from utils.web3_utils import W3_BY_CHAIN, call_with_retry, fetch_events_logs_with_retry
from web3.contract import Contract
from functools import partial
from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration

from constants.splice import (
    USDE_SY,
    USDE_YT,
    USDE_LPT,
    USDE_DEPLOYMENT_BLOCK,
    SUSDE_SY,
    SUSDE_YT,
    SUSDE_LPT,
    SUSDE_DEPLOYMENT_BLOCK,
)

w3 = W3_BY_CHAIN["mode"]["w3"]


########################################################################
# Contracts
########################################################################

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)

with open("abi/pendle_lpt.json") as f:
    lpt_abi = json.load(f)


usde_sy_contract = w3.eth.contract(address=USDE_SY, abi=erc20_abi)
usde_yt_contract = w3.eth.contract(address=USDE_YT, abi=erc20_abi)
usde_lpt_contract = w3.eth.contract(address=USDE_LPT, abi=lpt_abi)

susde_sy_contract = w3.eth.contract(address=SUSDE_SY, abi=erc20_abi)
susde_yt_contract = w3.eth.contract(address=SUSDE_YT, abi=erc20_abi)
susde_lpt_contract = w3.eth.contract(address=SUSDE_LPT, abi=lpt_abi)


########################################################################
# Get Balance Functions
########################################################################


def get_lpt_balance(
    user: str,
    block: int,
    sy_contract: Contract,
    lp_contract: Contract,
):
    sy_bal = call_with_retry(
        sy_contract.functions.balanceOf(lp_contract.address), block
    )
    if sy_bal == 0:
        return 0
    lpt_bal = call_with_retry(lp_contract.functions.activeBalance(user), block)
    if lpt_bal == 0:
        return 0
    total_active_supply = call_with_retry(
        lp_contract.functions.totalActiveSupply(), block
    )

    if total_active_supply == 0:
        print("total_active_supply is 0")
        return 0

    print(
        f"sy_bal: {sy_bal}, lpt_bal: {lpt_bal}, total_active_supply: {total_active_supply}"
    )
    print(round(((sy_bal / 10**18) * lpt_bal) / total_active_supply, 4))
    return round(((sy_bal / 10**18) * lpt_bal) / total_active_supply, 4)


def get_yt_balance(user: str, block: int, yt_contract: Contract) -> float:
    res = call_with_retry(yt_contract.functions.balanceOf(user), block)
    if not isinstance(res, (int, float)):
        return 0
    return round(res / 10**18, 4)


########################################################################
# Get Participants Functions
########################################################################


def get_splice_participants_v3(token_addresses, start: int):
    page_size = 1900
    all_users = set()
    target_block = w3.eth.get_block_number()

    for i in range(len(token_addresses)):
        token = token_addresses[i]
        contract = w3.eth.contract(address=token, abi=erc20_abi)

        while start < target_block:
            to_block = min(start + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"Splice v3 users {token}",
                contract.events.Transfer(),
                start,
                to_block,
            )
            print(start, to_block, len(transfers), "getting Splice contract data")
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
            start += page_size
    return all_users


########################################################################
# Configs
########################################################################

config = {
    IntegrationID.SPLICE_USDE_YT: {
        "chain": Chain.MODE,
        "start_block": USDE_DEPLOYMENT_BLOCK,
        "end_block": None,
        "sats_multiplier": 20,
        "token_addresses": [usde_yt_contract.address],
        "get_balance_func": partial(get_yt_balance, yt_contract=usde_yt_contract),
    },
    IntegrationID.SPLICE_USDE_LPT: {
        "chain": Chain.MODE,
        "start_block": USDE_DEPLOYMENT_BLOCK,
        "end_block": None,
        "sats_multiplier": 20,
        "token_addresses": [usde_sy_contract.address, usde_lpt_contract.address],
        "get_balance_func": partial(
            get_lpt_balance, sy_contract=usde_sy_contract, lp_contract=usde_lpt_contract
        ),
    },
    IntegrationID.SPLICE_SUSDE_YT: {
        "chain": Chain.MODE,
        "start_block": SUSDE_DEPLOYMENT_BLOCK,
        "end_block": None,
        "sats_multiplier": 20,
        "token_addresses": [susde_yt_contract.address],
        "get_balance_func": partial(get_yt_balance, yt_contract=susde_yt_contract),
    },
    IntegrationID.SPLICE_SUSDE_LPT: {
        "chain": Chain.MODE,
        "start_block": SUSDE_DEPLOYMENT_BLOCK,
        "end_block": None,
        "sats_multiplier": 20,
        "token_addresses": [susde_sy_contract.address, susde_lpt_contract.address],
        "get_balance_func": partial(
            get_lpt_balance,
            sy_contract=susde_sy_contract,
            lp_contract=susde_lpt_contract,
        ),
    },
}


########################################################################
# Integration Class
########################################################################


class SpliceIntegration(Integration):
    def __init__(self, integration_id: IntegrationID):
        super().__init__(
            integration_id,
            config[integration_id]["start_block"],
            config[integration_id]["chain"],
            None,  # SummaryColumn
            config[integration_id]["sats_multiplier"],  # SATS multiplier
            1,
            config[integration_id]["end_block"],
            None,  # reward multiplier fn
        )
        self.token_addresses = config[integration_id]["token_addresses"]
        self.get_balance_func = config[integration_id]["get_balance_func"]

    def get_description(self):
        return self.integration_id.get_description()

    def get_balance(self, user: str, block: int) -> float:
        logging.info(
            f"[{self.get_description()}] Getting balance for {user} at block {block}"
        )
        return self.get_balance_func(user, block)

    def get_participants(self) -> list:
        if self.participants is not None:
            return self.participants
        logging.info(f"[{self.get_description()}] Getting participants...")
        self.participants = get_splice_participants_v3(
            self.token_addresses, self.start_block
        )
        logging.info(
            f"[{self.get_description()}] Found {len(self.participants)} participants"
        )
        return self.participants
