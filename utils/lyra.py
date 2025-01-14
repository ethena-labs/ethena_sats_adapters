from utils.web3_utils import (
    W3_BY_CHAIN,
    fetch_events_logs_with_retry,
)
import os

import requests
from web3.contract import Contract
from utils.web3_utils import call_with_retry
from constants.chains import Chain
from web3 import Web3

url = "https://app.sentio.xyz/api/v1/graphql/derive/v2_subgraph"
SUSDE_VAULT_ADDRESS = Web3.to_checksum_address(
    "0x0b4eD379da8eF4FCF06F697c5782CA7b4c3E505E"
)

user_balance_query = """
{
  accounts(where: {or: [{id: "{user}"}, {owner: "{user}"}]}, block: {number: {block}}) {
    id
    owner
    subaccounts{
    subaccountId
    balances(where:{asset: "0x375804cdcf0d534fdd2657584a7c4ff5ab14a2bb000000000000000000000000"}){
        balance
    }
    }
    depositedSubaccounts{
    subaccountId
    balances(where:{asset: "0x375804cdcf0d534fdd2657584a7c4ff5ab14a2bb000000000000000000000000"}){
        balance
    }
    }
    }
}
"""


def get_exchange_balance(user: str, block: int) -> float:
    user = user.lower()
    # Replace the user and block placeholders in the query
    user_balance_query_filled = user_balance_query.replace("{user}", user).replace(
        "{block}", str(block)
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": str(os.getenv("DERIVE_SUBGRAPH_API_KEY", "")),
    }
    print(user_balance_query_filled)

    # Send the POST request
    response = requests.post(
        url, json={"query": user_balance_query_filled}, headers=headers
    )

    total_balance = 0.0
    if response.status_code == 200:
        response_json = response.json()
        accounts = response_json["data"]["accounts"]
        for account in accounts:
            for subaccount in account["subaccounts"]:
                for balance in subaccount["balances"]:
                    total_balance += float(balance["balance"])
            for subaccount in account["depositedSubaccounts"]:
                for balance in subaccount["balances"]:
                    total_balance += float(balance["balance"])
    else:
        print(f"Query failed with status code {response.status_code}: {response.text}")
    return total_balance


def get_effective_balance(
    user: str,
    block: int,
    integration_token: Contract,
    bridge: Contract,
    vault_token: Contract,
    timestamp,
):
    """
    Since vault tokens can be transferred, calculates the portion of totalSupply() of the vault held by user.

    User's effective ethena integration token balance = (vault.balanceOf(user) / vault.totalSupply()) * total bridge balance

    """
    user_vault_token_balance = call_with_retry(
        vault_token.functions.balanceOf(user), block
    )

    headers = {"Content-Type": "application/json"}

    # Send the POST request
    response = requests.post(
        "https://api.lyra.finance/public/get_vault_share",
        json={
            "from_timestamp_sec": 0,
            "to_timestamp_sec": timestamp,
            "vault_name": "sUSDePrincipal Protected Bull Call Spread",
            "page_size": 1,
        },
        headers=headers,
    )
    try:
        response_json = response.json()
        vault_price = float(response_json["result"]["vault_shares"][0]["base_value"])
    except:
        print("Failed to get vault price, using default")
        vault_price = float(1)

    return user_vault_token_balance * vault_price / 1e18


all_users_query = """
{
  subAccountBalances(where: {asset: "0x375804cdcf0d534fdd2657584a7c4ff5ab14a2bb000000000000000000000000"} first: 1000) {
    subaccount {
      id
      owner {
        id
        owner
      }
      matchingOwner {
        id
        owner
      }
    }
  }
}
"""


def get_exchange_users() -> set:
    headers = {
        "Content-Type": "application/json",
        "api-key": str(os.getenv("DERIVE_SUBGRAPH_API_KEY", "")),
    }

    response = requests.post(url, json={"query": all_users_query}, headers=headers)

    users = set()
    if response.status_code == 200:
        response_json = response.json()
        balances = response_json["data"]["subAccountBalances"]
        for balance in balances:
            if balance["subaccount"]["matchingOwner"] is not None:
                if balance["subaccount"]["matchingOwner"]["owner"] is not None:
                    users.add(
                        Web3.to_checksum_address(
                            balance["subaccount"]["matchingOwner"]["owner"]
                        )
                    )
                else:
                    users.add(
                        Web3.to_checksum_address(
                            balance["subaccount"]["matchingOwner"]["id"]
                        )
                    )
            else:
                if balance["subaccount"]["owner"]["owner"] is not None:
                    users.add(
                        Web3.to_checksum_address(
                            balance["subaccount"]["owner"]["owner"]
                        )
                    )
                else:
                    users.add(
                        Web3.to_checksum_address(balance["subaccount"]["owner"]["id"])
                    )
    else:
        print(f"Query failed with status code {response.status_code}: {response.text}")

    try:
        users.remove(
            SUSDE_VAULT_ADDRESS
        )  # Ignore the sUSDe vault which is accounted for separately
    except:
        pass

    return users


def get_vault_users(
    start_block: int, page_size: int, vault_token: Contract, chain: Chain
):
    """
    Gets all participants that have ever interacted with the vault token by fetching all vault transfer events.

    Note: does not support cross-chain bridging of vault tokens.
    """
    all_users = set()

    target_block = W3_BY_CHAIN[chain]["w3"].eth.get_block_number()

    while start_block < target_block:
        to_block = min(start_block + page_size, target_block)
        event_label = f"Getting Lyra participants from {start_block} to {to_block}"

        transfers = fetch_events_logs_with_retry(
            event_label,
            vault_token.events.Transfer(),
            start_block,
            to_block,
        )
        print(event_label, ": found", len(transfers), "transfers")
        for transfer in transfers:
            all_users.add(transfer["args"]["to"])
        start_block += page_size
    return all_users
