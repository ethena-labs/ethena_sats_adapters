from utils.web3_utils import (
    W3_BY_CHAIN,
    fetch_events_logs_with_retry,
)

from web3.contract import Contract
from utils.web3_utils import call_with_retry
from constants.chains import Chain


def get_effective_balance(user: str, block: int, integration_token: Contract, bridge: Contract, vault_token: Contract):
    """ "
    Returns the effective Ethena integration token balance.
    Since vault-tokens can be transfered, calculates the portion of total vault token balance held by user.

    User's effective ethena integration token balance = % of vault token owned * total bridge balance

    """
    total_bridge_balance = call_with_retry(integration_token.functions.balanceOf(bridge.address), block)
    total_vault_token_balance = call_with_retry(vault_token.functions.totalSupply(), block)
    user_vault_token_balance = call_with_retry(vault_token.functions.balanceOf(user), block)
    return (user_vault_token_balance / total_vault_token_balance) * total_bridge_balance


def get_vault_users(start_block: int, page_size: int, vault_token: Contract, chain: Chain):
    """
    Gets all participants that have ever interacted with the vault token.

    Note: does not support cross-chain bridging of vault tokens.
    """
    all_users = set()

    target_block = W3_BY_CHAIN[chain].eth.get_block_number()

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
