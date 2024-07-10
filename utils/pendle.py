import os
import json
from dotenv import load_dotenv
from utils.web3_utils import (
    W3_BY_CHAIN,
    fetch_events_logs_with_retry,
    w3,
    w3_mantle,
    w3_arb,
)
from constants.chains import Chain

from constants.pendle import (
    LPT,
    PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
    PENDLE_SUSDE_JULY_DEPLOYMENT_BLOCK,
    PENDLE_SUSDE_SEPT_DEPLOYMENT_BLOCK,
    SY,
    YT,
    pendle_router,
    sUSDe_LPT,
    sUSDe_SY,
    sUSDe_YT,
    SUSDE_LPT_SEPT,
    SUSDE_SY_SEPT,
    SUSDE_YT_SEPT,
    sUSDe_LPT_old,
    sUSDe_SY_old,
    sUSDe_YT_old,
    mantle_LPT,
    mantle_SY,
    mantle_YT,
    USDe_zircuit_LPT,
    USDe_zircuit_SY,
    USDe_zircuit_YT,
    ENA_LP,
    ENA_SY,
    ENA_YT,
    usde_arb_LP,
    usde_arb_SY,
    usde_arb_YT,
    PENDLE_USDE_KARAK_LP,
    PENDLE_USDE_KARAK_SY,
    PENDLE_USDE_KARAK_YT,
    PENDLE_SUSDE_KARAK_LP,
    PENDLE_SUSDE_KARAK_SY,
    PENDLE_SUSDE_KARAK_YT,
    PENDLE_USDE_ARB_DEPLOYMENT_BLOCK,
    PENDLE_USDE_KARAK_DEPLOYMENT_BLOCK,
    PENDLE_SUSDE_KARAK_DEPLOYMENT_BLOCK,
    PENDLE_MANTLE_DEPLOYMENT_BLOCK,
    PENDLE_ENA_DEPLOYMENT_BLOCK,
    PENDLE_USDE_ZIRCUIT_DEPLOYMENT_BLOCK,
    PENDLE_SUSDE_APRIL_DEPLOYMENT_BLOCK,
)

load_dotenv()

FOLDER = os.getenv("FOLDER")

with open("abi/pendle_lpt.json") as f:
    lpt_abi = json.load(f)

with open("abi/pendle_router_abi.json") as f:
    pendle_router_abi = json.load(f)

with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


lpt_contract = w3.eth.contract(address=LPT, abi=lpt_abi)
sy_contract = w3.eth.contract(address=SY, abi=erc20_abi)
yt_contract = w3.eth.contract(address=YT, abi=erc20_abi)
pendle_router_contract = w3.eth.contract(address=pendle_router, abi=pendle_router_abi)


susde_lpt_contract = w3.eth.contract(address=sUSDe_LPT, abi=lpt_abi)
susde_sy_contract = w3.eth.contract(address=sUSDe_SY, abi=erc20_abi)
susde_yt_contract = w3.eth.contract(address=sUSDe_YT, abi=erc20_abi)


SUSDE_SY_SEPT_CONTRACT = w3.eth.contract(address=SUSDE_SY_SEPT, abi=erc20_abi)
SUSDE_YT_SEPT_CONTRACT = w3.eth.contract(address=SUSDE_YT_SEPT, abi=erc20_abi)
SUSDE_LPT_SEPT_CONTRACT = w3.eth.contract(address=SUSDE_LPT_SEPT, abi=lpt_abi)


susde_lpt_contract_old = w3.eth.contract(address=sUSDe_LPT_old, abi=lpt_abi)
susde_sy_contract_old = w3.eth.contract(address=sUSDe_SY_old, abi=erc20_abi)
susde_yt_contract_old = w3.eth.contract(address=sUSDe_YT_old, abi=erc20_abi)


mantle_lpt_contract = w3_mantle.eth.contract(address=mantle_LPT, abi=lpt_abi)
mantle_sy_contract = w3_mantle.eth.contract(address=mantle_SY, abi=erc20_abi)
mantle_yt_contract = w3_mantle.eth.contract(address=mantle_YT, abi=erc20_abi)


USDe_zircuit_LPT_contract = w3.eth.contract(address=USDe_zircuit_LPT, abi=lpt_abi)
USDe_zircuit_SY_contract = w3.eth.contract(address=USDe_zircuit_SY, abi=erc20_abi)
USDe_zircuit_YT_contract = w3.eth.contract(address=USDe_zircuit_YT, abi=erc20_abi)


ENA_LPT_contract = w3.eth.contract(address=ENA_LP, abi=lpt_abi)
ENA_SY_contract = w3.eth.contract(address=ENA_SY, abi=erc20_abi)
ENA_YT_contract = w3.eth.contract(address=ENA_YT, abi=erc20_abi)


PENDLE_USDE_KARAK_LP_CONTRACT = w3.eth.contract(
    address=PENDLE_USDE_KARAK_LP, abi=lpt_abi
)
PENDLE_USDE_KARAK_SY_CONTRACT = w3.eth.contract(
    address=PENDLE_USDE_KARAK_SY, abi=erc20_abi
)
PENDLE_USDE_KARAK_YT_CONTRACT = w3.eth.contract(
    address=PENDLE_USDE_KARAK_YT, abi=erc20_abi
)


PENDLE_SUSDE_KARAK_LP_CONTRACT = w3.eth.contract(
    address=PENDLE_SUSDE_KARAK_LP, abi=lpt_abi
)
PENDLE_SUSDE_KARAK_SY_CONTRACT = w3.eth.contract(
    address=PENDLE_SUSDE_KARAK_SY, abi=erc20_abi
)
PENDLE_SUSDE_KARAK_YT_CONTRACT = w3.eth.contract(
    address=PENDLE_SUSDE_KARAK_YT, abi=erc20_abi
)

usde_arb_LPT_contract = w3_arb.eth.contract(address=usde_arb_LP, abi=lpt_abi)
usde_arb_SY_contract = w3_arb.eth.contract(address=usde_arb_SY, abi=erc20_abi)
usde_arb_YT_contract = w3_arb.eth.contract(address=usde_arb_YT, abi=erc20_abi)

PENDLE_CONTRACT_AND_START_BY_LP_TOKEN = {
    SY: {
        "start": PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        "contract": sy_contract,
        "chain": Chain.ETHEREUM,
        "type": "sy",
    },
    LPT: {
        "start": PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        "contract": lpt_contract,
        "chain": Chain.ETHEREUM,
        "type": "lpt",
        "sats": 20,
    },
    YT: {
        "start": PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        "contract": yt_contract,
        "chain": Chain.ETHEREUM,
        "type": "yt",
    },
    sUSDe_LPT: {
        "start": PENDLE_SUSDE_JULY_DEPLOYMENT_BLOCK,
        "contract": susde_lpt_contract,
        "chain": Chain.ETHEREUM,
        "type": "lpt",
        "sats": 20,
    },
    sUSDe_SY: {
        "start": PENDLE_SUSDE_JULY_DEPLOYMENT_BLOCK,
        "contract": susde_sy_contract,
        "chain": Chain.ETHEREUM,
        "type": "sy",
    },
    sUSDe_YT: {
        "start": PENDLE_SUSDE_JULY_DEPLOYMENT_BLOCK,
        "contract": susde_yt_contract,
        "chain": Chain.ETHEREUM,
        "type": "yt",
    },
    SUSDE_LPT_SEPT: {
        "start": PENDLE_SUSDE_SEPT_DEPLOYMENT_BLOCK,
        "contract": SUSDE_LPT_SEPT_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "lpt",
        "sats": 20,
    },
    SUSDE_SY_SEPT: {
        "start": PENDLE_SUSDE_SEPT_DEPLOYMENT_BLOCK,
        "contract": SUSDE_SY_SEPT_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "sy",
    },
    SUSDE_YT_SEPT: {
        "start": PENDLE_SUSDE_SEPT_DEPLOYMENT_BLOCK,
        "contract": SUSDE_YT_SEPT_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "yt",
    },
    sUSDe_LPT_old: {
        "start": PENDLE_SUSDE_APRIL_DEPLOYMENT_BLOCK,
        "contract": susde_lpt_contract_old,
        "chain": Chain.ETHEREUM,
        "type": "lpt",
        "sats": 5,
    },
    sUSDe_SY_old: {
        "start": PENDLE_SUSDE_APRIL_DEPLOYMENT_BLOCK,
        "contract": susde_sy_contract_old,
        "chain": Chain.ETHEREUM,
        "type": "sy",
    },
    sUSDe_YT_old: {
        "start": PENDLE_SUSDE_APRIL_DEPLOYMENT_BLOCK,
        "contract": susde_yt_contract_old,
        "chain": Chain.ETHEREUM,
        "type": "yt",
    },
    mantle_LPT: {
        "start": PENDLE_MANTLE_DEPLOYMENT_BLOCK,
        "contract": mantle_lpt_contract,
        "chain": Chain.MANTLE,
        "type": "lpt",
        "sats": 20,
    },
    mantle_SY: {
        "start": PENDLE_MANTLE_DEPLOYMENT_BLOCK,
        "contract": mantle_sy_contract,
        "chain": Chain.MANTLE,
        "type": "sy",
    },
    mantle_YT: {
        "start": PENDLE_MANTLE_DEPLOYMENT_BLOCK,
        "contract": mantle_yt_contract,
        "chain": Chain.MANTLE,
        "type": "yt",
    },
    USDe_zircuit_LPT: {
        "start": PENDLE_USDE_ZIRCUIT_DEPLOYMENT_BLOCK,
        "contract": USDe_zircuit_LPT_contract,
        "chain": Chain.ETHEREUM,
        "type": "lpt",
        "sats": 20,
    },
    USDe_zircuit_SY: {
        "start": PENDLE_USDE_ZIRCUIT_DEPLOYMENT_BLOCK,
        "contract": USDe_zircuit_SY_contract,
        "chain": Chain.ETHEREUM,
        "type": "sy",
    },
    USDe_zircuit_YT: {
        "start": PENDLE_USDE_ZIRCUIT_DEPLOYMENT_BLOCK,
        "contract": USDe_zircuit_YT_contract,
        "chain": Chain.ETHEREUM,
        "type": "yt",
    },
    ENA_LP: {
        "start": PENDLE_ENA_DEPLOYMENT_BLOCK,
        "contract": ENA_LPT_contract,
        "chain": Chain.ETHEREUM,
        "type": "lpt",
        "sats": 30,
    },
    ENA_YT: {
        "start": PENDLE_ENA_DEPLOYMENT_BLOCK,
        "contract": ENA_YT_contract,
        "chain": Chain.ETHEREUM,
        "type": "yt",
    },
    ENA_SY: {
        "start": PENDLE_ENA_DEPLOYMENT_BLOCK,
        "contract": ENA_SY_contract,
        "chain": Chain.ETHEREUM,
        "type": "sy",
    },
    usde_arb_LP: {
        "start": PENDLE_USDE_ARB_DEPLOYMENT_BLOCK,
        "contract": usde_arb_LPT_contract,
        "chain": Chain.ARBITRUM,
        "type": "lpt",
        "sats": 20,
    },
    usde_arb_SY: {
        "start": PENDLE_USDE_ARB_DEPLOYMENT_BLOCK,
        "contract": usde_arb_SY_contract,
        "chain": Chain.ARBITRUM,
        "type": "sy",
    },
    usde_arb_YT: {
        "start": PENDLE_USDE_ARB_DEPLOYMENT_BLOCK,
        "contract": usde_arb_YT_contract,
        "chain": Chain.ARBITRUM,
        "type": "yt",
    },
    PENDLE_USDE_KARAK_LP: {
        "start": PENDLE_USDE_KARAK_DEPLOYMENT_BLOCK,
        "contract": PENDLE_USDE_KARAK_LP_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "lpt",
        "sats": 20,
    },
    PENDLE_USDE_KARAK_SY: {
        "start": PENDLE_USDE_KARAK_DEPLOYMENT_BLOCK,
        "contract": PENDLE_USDE_KARAK_SY_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "sy",
    },
    PENDLE_USDE_KARAK_YT: {
        "start": PENDLE_USDE_KARAK_DEPLOYMENT_BLOCK,
        "contract": PENDLE_USDE_KARAK_YT_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "yt",
    },
    PENDLE_SUSDE_KARAK_LP: {
        "start": PENDLE_SUSDE_KARAK_DEPLOYMENT_BLOCK,
        "contract": PENDLE_SUSDE_KARAK_LP_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "lpt",
        "sats": 5,
    },
    PENDLE_SUSDE_KARAK_SY: {
        "start": PENDLE_SUSDE_KARAK_DEPLOYMENT_BLOCK,
        "contract": PENDLE_SUSDE_KARAK_SY_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "sy",
    },
    PENDLE_SUSDE_KARAK_YT: {
        "start": PENDLE_SUSDE_KARAK_DEPLOYMENT_BLOCK,
        "contract": PENDLE_SUSDE_KARAK_YT_CONTRACT,
        "chain": Chain.ETHEREUM,
        "type": "yt",
    },
}


def get_pendle_participants_v3(token_addresses):
    all_users = set()
    for token in token_addresses:
        token_data = PENDLE_CONTRACT_AND_START_BY_LP_TOKEN[token]
        if not token_data:
            continue
        start = token_data["start"]
        contract = token_data["contract"]
        chain = token_data["chain"]
        web3_for_token = W3_BY_CHAIN[chain]
        page_size = 1900
        target_block = web3_for_token.eth.get_block_number()
        while start < target_block:
            to_block = min(start + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"Pendle v3 users {token}",
                contract.events.Transfer(),
                start,
                to_block,
            )
            print(start, to_block, len(transfers), "getting Pendle contract data")
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
            start += page_size
    return all_users
