from utils.request_utils import requests_retry_session
from constants.felix import FELIX_USDE_VAULT_CONTRACT
from typing import Dict
from web3.types import ChecksumAddress
from web3 import Web3


def get_shares_to_assets_ratio_at_block(block_number: int) -> float:
    """
    Get the ratio of shares to assets for the Felix USDe vault at a specific block.
    """
    shares_base_amount = 100000000000000000000000
    try:
        # Call convertToAssets with shares_base_amount to get the ratio
        result = FELIX_USDE_VAULT_CONTRACT.functions.convertToAssets(shares_base_amount).call(
            block_identifier=block_number
        )
        return result / (shares_base_amount)
    except Exception as e:
        print(f"Error getting shares to assets ratio: {e}")
        return 0.0


def get_users_asset_balances_at_block(block_number: int) -> Dict[ChecksumAddress, float]:
    """
    Get users' asset balances at a specific block by:
    1. Retrieving active holders' shares from subgraph
    2. Applying shares-to-assets ratio to convert shares to assets
    3. Returning a dictionary mapping user addresses to their asset balances in USDe
    
    Args:
        block_number: Block number to query
        batch_size: Number of users to process in each multicall batch (default: 400)
    """
    # Get active holders' shares from subgraph
    from constants.felix import FELIX_USDE_HOLDERS_GRAPH_URL
    active_holders_shares = get_feUSDe_active_holders_balance_at_block(
        FELIX_USDE_HOLDERS_GRAPH_URL, block_number
    )
    if not active_holders_shares:
        return {}

    # Get the shares-to-assets ratio for this block
    shares_to_assets_ratio = get_shares_to_assets_ratio_at_block(block_number)

    # Convert shares to assets using the ratio
    user_asset_balances = {}

    for user_address, shares in active_holders_shares.items():
        # Convert string address to ChecksumAddress
        checksum_address = Web3.to_checksum_address(user_address)
        # Apply ratio to convert shares to assets
        asset_balance = shares * shares_to_assets_ratio / (10 ** 18)
        user_asset_balances[checksum_address] = asset_balance
        
    return user_asset_balances


def get_feUSDe_active_holders_balance_at_block(graph_url: str, block_number: int):
    skip = 0
    max_pagination_size = 1000
    active_holders_balance = {}

    session = requests_retry_session(
        retries=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504)
    )

    while True:
        query = """
        {
            accounts(first: %s, skip: %s) {
                id
                snapshots(
                    where: {blockNumber_lte: %s}
                    orderBy: blockNumber
                    orderDirection: desc
                    first: 1
                ) {
                    balance
                }
            }
        }
        """ % (max_pagination_size, skip, block_number)

        response = session.post(
            url=graph_url,
            json={'query': query},
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

        data = response.json()
        accounts = data['data']['accounts']

        if not accounts:
            break

        for account in accounts:
            # Only include accounts with a positive balance at the block number
            if account['snapshots'] and int(account['snapshots'][0]['balance']) > 0:
                active_holders_balance[account['id']] = int(account['snapshots'][0]['balance'])

        # Stop if we've reached the end of the accounts
        if len(accounts) < max_pagination_size:
            break

        skip += max_pagination_size

    return active_holders_balance
