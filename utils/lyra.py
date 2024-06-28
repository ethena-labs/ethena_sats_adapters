from utils.web3_utils import (
    W3_BY_CHAIN,
    fetch_events_logs_with_retry,
    w3,
    w3_mantle,
    w3_arb,
)

from constants.lyra import LYRA_CONTRACTS_AND_START_BY_TOKEN


# Balance Process
# 1. Get total bridge balance
# 2. Get total vault token balance
# 3. Get user vault token balance
# 4. Balance = (3 / 2) * 1


def get_lyra_participants(vault_token_name: str):
    """
    Gets all participants that have ever interacted with the vault token
    """
    all_users = set()
    vault_data = LYRA_CONTRACTS_AND_START_BY_TOKEN[vault_token_name]
    if not vault_data:
        return all_users

    start = vault_data["start"]
    page_size = 1000
    target_block = W3_BY_CHAIN[vault_data["chain"]]["w3"].eth.get_block_number()

    event_label = f"Getting Lyra participants for: {vault_token_name}"
    while start < target_block:
        to_block = min(start + page_size, target_block)
        transfers = fetch_events_logs_with_retry(
            event_label,
            vault_data["vault_token"].events.Transfer(),
            start,
            to_block,
        )
        print(event_label, start, to_block, len(transfers))
        for transfer in transfers:
            all_users.add(transfer["args"]["to"])
        start += page_size
    return all_users
