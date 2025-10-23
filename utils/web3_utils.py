import logging
import os
import time
from datetime import datetime
import traceback
from typing import Iterable, List, Tuple, Union

from dotenv import load_dotenv
from eth_abi.abi import decode

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import BlockIdentifier, EventData

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
FRAXTAL_NODE_URL = os.getenv("FRAXTAL_NODE_URL")
w3_fraxtal = Web3(Web3.HTTPProvider(FRAXTAL_NODE_URL))
LYRA_NODE_URL = os.getenv("LYRA_NODE_URL")
w3_lyra = Web3(Web3.HTTPProvider(LYRA_NODE_URL))
SWELL_NODE_URL = os.getenv("SWELL_NODE_URL")
w3_swell = Web3(Web3.HTTPProvider(SWELL_NODE_URL))
BASE_NODE_URL = os.getenv("BASE_NODE_URL")
w3_base = Web3(Web3.HTTPProvider(BASE_NODE_URL))
SEPOLIA_NODE_URL = os.getenv("SEPOLIA_NODE_URL")
w3_sepolia = Web3(Web3.HTTPProvider(SEPOLIA_NODE_URL))
HYPEREVM_NODE_URL = os.getenv("HYPEREVM_NODE_URL")
w3_hyperevm = Web3(Web3.HTTPProvider(HYPEREVM_NODE_URL))
PLASMA_NODE_URL = os.getenv("PLASMA_NODE_URL")
w3_plasma = Web3(Web3.HTTPProvider(PLASMA_NODE_URL))
BERACHAIN_NODE_URL = os.getenv("BERACHAIN_NODE_URL")
w3_berachain = Web3(Web3.HTTPProvider(BERACHAIN_NODE_URL))

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
    Chain.FRAXTAL: {
        "w3": w3_fraxtal,
    },
    Chain.LYRA: {
        "w3": w3_lyra,
    },
    Chain.SWELL: {
        "w3": w3_swell,
    },
    Chain.SOLANA: {
        "w3": w3,
    },
    Chain.TON: {
        "w3": w3,
    },
    Chain.BASE: {
        "w3": w3_base,
    },
    Chain.SEPOLIA: {
        "w3": w3_sepolia,
    },
    Chain.HYPEREVM: {
        "w3": w3_hyperevm,
    },
    Chain.PLASMA: {
        "w3": w3_plasma,
    },
    Chain.BERACHAIN: {
        "w3": w3_berachain,
    },
}

MULTICALL_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "target", "type": "address"},
                    {"internalType": "bytes", "name": "callData", "type": "bytes"},
                ],
                "internalType": "struct Multicall3.Call[]",
                "name": "calls",
                "type": "tuple[]",
            }
        ],
        "name": "aggregate",
        "outputs": [
            {"internalType": "uint256", "name": "blockNumber", "type": "uint256"},
            {"internalType": "bytes[]", "name": "returnData", "type": "bytes[]"},
        ],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "target", "type": "address"},
                    {"internalType": "bool", "name": "allowFailure", "type": "bool"},
                    {"internalType": "bytes", "name": "callData", "type": "bytes"},
                ],
                "internalType": "struct Multicall3.Call3[]",
                "name": "calls",
                "type": "tuple[]",
            }
        ],
        "name": "aggregate3",
        "outputs": [
            {
                "components": [
                    {"internalType": "bool", "name": "success", "type": "bool"},
                    {"internalType": "bytes", "name": "returnData", "type": "bytes"},
                ],
                "internalType": "struct Multicall3.Result[]",
                "name": "returnData",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "payable",
        "type": "function",
    },
]

MULTICALL_ADDRESS = (
    "0xcA11bde05977b3631167028862bE2a173976CA11"  # Ethereum mainnet address
)
MULTICALL_ADDRESS_BY_CHAIN = {
    Chain.SWELL: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Chain.SEPOLIA: "0x25Eef291876194AeFAd0D60Dff89e268b90754Bb",
    Chain.ETHEREUM: MULTICALL_ADDRESS,
    Chain.HYPEREVM: "0xcA11bde05977b3631167028862bE2a173976CA11",
    Chain.BLAST: Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11"),
}


def fetch_events_logs_with_retry(
    label: str,
    contract_event,
    from_block: int,
    to_block: int | str = "latest",
    retries: int = 3,
    delay: int = 2,
    # pylint: disable=redefined-builtin
    filter: dict | None = None,
) -> Iterable[EventData]:
    for attempt in range(retries):
        try:
            if filter is None:
                return contract_event.get_logs(fromBlock=from_block, toBlock=to_block)
            else:
                return contract_event.get_logs(
                    fromBlock=from_block, toBlock=to_block, argument_filters=filter
                )

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            else:
                msg = f"Error getting events logs for {label}: {e}, {traceback.format_exc()}"
                logging.error(msg)
                slack_message(msg)
                raise e
    return {}


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
                slack_message(msg)
                raise e


# pylint: disable=redefined-outer-name
def multicall(w3: Web3, calls: list, block_identifier: BlockIdentifier = "latest"):
    multicall_contract = w3.eth.contract(
        address=Web3.to_checksum_address(MULTICALL_ADDRESS), abi=MULTICALL_ABI
    )

    aggregate_calls = []
    for call in calls:
        contract, fn_name, args = call
        call_data = contract.encode_abi(fn_name=fn_name, args=args)
        aggregate_calls.append((contract.address, call_data))

    result = multicall_contract.functions.aggregate(aggregate_calls).call(
        block_identifier=block_identifier
    )

    decoded_results = []
    for i, call in enumerate(calls):
        contract, fn_name, _ = call
        function = contract.get_function_by_name(fn_name)
        output_types = [output["type"] for output in function.abi["outputs"]]
        decoded_results.append(decode(output_types, result[1][i]))

    return decoded_results


def multicall_by_address(
    wb3: Web3,
    multical_address: str,
    calls: list,
    block_identifier="latest",
    allow_failure: bool = False,
    batch_size: int = 1024,
):
    multicall_contract = wb3.eth.contract(
        address=Web3.to_checksum_address(multical_address), abi=MULTICALL_ABI
    )

    aggregate_calls: List[
        Union[Tuple[ChecksumAddress, bool, str], Tuple[ChecksumAddress, str]]
    ] = []
    for call in calls:
        contract, fn_name, args = call
        call_data = contract.encode_abi(fn_name, args=args)

        aggregate_calls.append((contract.address, allow_failure, call_data))

    result = []
    for i in range(0, len(aggregate_calls), batch_size):
        batch = aggregate_calls[i : i + batch_size]

        if allow_failure:
            # When allowing failures, catch contract reverts and return None for failed batches
            try:
                batch_result = call_with_retry(
                    multicall_contract.functions.aggregate3(batch),
                    block=block_identifier,
                )
                result.extend(batch_result)
            except Exception as e:
                print(
                    f"Multicall batch failed, returning None for {len(batch)} calls: {e}"
                )
                # Return None for each call in the failed batch
                result.extend([(False, b"")] * len(batch))
        else:
            result.extend(
                call_with_retry(
                    multicall_contract.functions.aggregate3(batch),
                    block=block_identifier,
                )
            )

    decoded_results: List[Union[Tuple, None]] = []
    for i, call in enumerate(calls):
        contract, fn_name, _ = call
        function = contract.get_function_by_name(fn_name)
        output_types = [output["type"] for output in function.abi["outputs"]]
        if allow_failure:
            success = result[i][0]
            if success:
                decoded_output = decode(output_types, result[i][1])
                decoded_results.append(decoded_output)
            else:
                decoded_results.append(None)
        else:
            decoded_output = decode(output_types, result[i][1])
            decoded_results.append(decoded_output)

    return decoded_results


def get_block_date(
    block: int, chain: Chain, adjustment: int = 0, fmt: str = "%Y-%m-%d %H"
) -> str:
    wb3 = W3_BY_CHAIN[chain]["w3"]
    block_info = wb3.eth.get_block(block)
    timestamp = (
        block_info["timestamp"]
        if adjustment == 0
        else block_info["timestamp"] - adjustment
    )
    timestamp_date = datetime.fromtimestamp(timestamp).strftime(fmt)
    return timestamp_date


def fetch_transaction_receipt_with_retry(
    chain: Chain, transaction_hash, retries=3, delay=2
):
    wb3 = W3_BY_CHAIN[chain]["w3"]
    for attempt in range(retries):
        try:
            return wb3.eth.get_transaction_receipt(transaction_hash)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            else:
                msg = f"Error fetching transaction: {e}, {traceback.format_exc()}"
                logging.error(msg)
                slack_message(msg)
                raise e
