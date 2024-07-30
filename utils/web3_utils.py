import logging
import os
import time
import traceback

from dotenv import load_dotenv
from web3 import Web3

from utils.slack import slack_message
from constants.chains import Chain

load_dotenv()
ETH_NODE_URL = os.getenv("ETH_NODE_URL")
w3 = Web3(Web3.HTTPProvider(ETH_NODE_URL))
ARBITRUM_NODE_URL = os.getenv("ARBITRUM_NODE_URL")
w3_arb = Web3(Web3.HTTPProvider(ARBITRUM_NODE_URL))
MANTLE_NODE_URL = os.getenv("MANTLE_NODE_URL")
w3_mantle = Web3(Web3.HTTPProvider(MANTLE_NODE_URL))
BLAST_NODE_URL = os.getenv("BLAST_NODE_URL")
w3_blast = Web3(Web3.HTTPProvider(BLAST_NODE_URL))
SCROLL_NODE_URL = os.getenv("SCROLL_NODE_URL")
w3_scroll = Web3(Web3.HTTPProvider(SCROLL_NODE_URL))
MODE_NODE_URL = os.getenv("MODE_NODE_URL")
w3_mode = Web3(Web3.HTTPProvider(MODE_NODE_URL))

W3_BY_CHAIN = {
    Chain.ETHEREUM: {
        "w3": w3,
    },
    Chain.ARBITRUM: {
        "w3": w3_arb,
    },
    Chain.MANTLE: {
        "w3": w3_mantle,
    },
    Chain.BLAST: {
        "w3": w3_blast,
    },
    Chain.SCROLL: {
        "w3": w3_scroll,
    },
    Chain.MODE: {
        "w3": w3_mode,
    },
}


def fetch_events_logs_with_retry(
    label: str,
    contract_event,
    from_block: int,
    to_block: int = "latest",
    retries: int = 3,
    delay: int = 2,
    filter: dict = None,
) -> dict:
    for attempt in range(retries):
        try:
            if filter is None:
                return contract_event.get_logs(fromBlock=from_block, toBlock=to_block)
            else:
                return contract_event.get_logs(filter)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            else:
                msg = f"Error getting events logs for {label}: {e}, {traceback.format_exc()}"
                logging.error(msg)
                slack_message(msg)
                raise e


def call_with_retry(contract_function, block="latest", retries=3, delay=2):
    for attempt in range(retries):
        try:
            return contract_function.call(block_identifier=block)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            else:
                msg = f"Error calling function: {e}, {traceback.format_exc()}"
                logging.error(msg)
                #slack_message(msg)
                raise e
