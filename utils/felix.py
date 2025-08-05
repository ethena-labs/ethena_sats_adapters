from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.request_utils import requests_retry_session
from utils.web3_utils import multicall_by_address, W3_BY_CHAIN, MULTICALL_ADDRESS_BY_CHAIN
from constants.chains import Chain
from constants.felix import FELIX_USDE_VAULT_CONTRACT
from typing import Dict, List, Tuple
from web3.types import ChecksumAddress
from web3 import Web3


def get_users_asset_balances_at_block(block_number: int, batch_size: int = 24) -> Dict[ChecksumAddress, float]:
    """
    Get users' asset balances at a specific block by:
    1. Retrieving active holders' shares from subgraph
    2. Converting shares to assets using multicall (batched for large user sets)
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
    
    # Convert to lists for easier batching
    user_addresses = list(active_holders_shares.keys())
    shares_list = list(active_holders_shares.values())
    
    # Initialize result dictionary
    user_asset_balances = {}
    
    # Process users in batches
    w3 = W3_BY_CHAIN[Chain.HYPEREVM]["w3"]
    hyperevm_multicall_address = MULTICALL_ADDRESS_BY_CHAIN[Chain.HYPEREVM]
    
    for i in range(0, len(user_addresses), batch_size):
        # Get current batch
        batch_addresses = user_addresses[i:i + batch_size]
        batch_shares = shares_list[i:i + batch_size]
        
        # Prepare multicall for this batch
        calls = []
        for shares in batch_shares:
            calls.append((FELIX_USDE_VAULT_CONTRACT, "convertToAssets", [shares]))
        
        # Execute multicall for this batch
        try:
            asset_balances = multicall_by_address(
                w3, hyperevm_multicall_address, calls, block_identifier=block_number
            )
            # Process results for this batch
            for j, user_address in enumerate(batch_addresses):
                # Convert string address to ChecksumAddress
                checksum_address = Web3.to_checksum_address(user_address)
                # Convert wei to USDe (assuming 18 decimals)
                asset_balance_wei = asset_balances[j][0]
                asset_balance_usde = asset_balance_wei / (10 ** 18)
                user_asset_balances[checksum_address] = asset_balance_usde
                
        except Exception as e:
            print(f"Warning: Failed to process batch {i//batch_size + 1} for users {i} to {i + len(batch_addresses)}: {e}")
            # Continue with next batch instead of failing completely
            continue
    
    return user_asset_balances


def _process_batch(
    batch_data: Tuple[List[str], List[int]], 
    block_number: int,
    batch_index: int
) -> Tuple[int, Dict[ChecksumAddress, float]]:
    """
    Process a single batch of users. This function is designed to be called by threads.
    
    Args:
        batch_data: Tuple of (user_addresses, shares_list)
        block_number: Block number to query
        batch_index: Index of the batch for logging
        
    Returns:
        Tuple of (batch_index, user_balances_dict)
    """
    batch_addresses, batch_shares = batch_data
    
    # Initialize Web3 and multicall contract for this thread
    w3 = W3_BY_CHAIN[Chain.HYPEREVM]["w3"]
    hyperevm_multicall_address = MULTICALL_ADDRESS_BY_CHAIN[Chain.HYPEREVM]
    
    # Prepare multicall for this batch
    calls = []
    for shares in batch_shares:
        calls.append((FELIX_USDE_VAULT_CONTRACT, "convertToAssets", [shares]))
    
    # Execute multicall for this batch
    try:
        asset_balances = multicall_by_address(
            w3, hyperevm_multicall_address, calls, block_identifier=block_number
        )
        
        # Process results for this batch
        batch_results = {}
        for j, user_address in enumerate(batch_addresses):
            # Convert string address to ChecksumAddress
            checksum_address = Web3.to_checksum_address(user_address)
            # Convert wei to USDe (assuming 18 decimals)
            asset_balance_wei = asset_balances[j][0]
            asset_balance_usde = asset_balance_wei / (10 ** 18)
            batch_results[checksum_address] = asset_balance_usde
        
        print(f"✓ Batch {batch_index + 1} completed successfully ({len(batch_addresses)} users)")
        return batch_index, batch_results
        
    except Exception as e:
        print(f"✗ Batch {batch_index + 1} failed: {e}")
        return batch_index, {}


def get_users_asset_balances_at_block_multithreaded(
    block_number: int, 
    batch_size: int = 25, 
    max_workers: int = 20
) -> Dict[ChecksumAddress, float]:
    """
    Get users' asset balances using multithreading for parallel processing.
    
    Args:
        block_number: Block number to query
        batch_size: Number of users to process in each multicall batch (default: 24)
        max_workers: Maximum number of worker threads (default: 4)
    """
    # Get active holders' shares from subgraph
    from constants.felix import FELIX_USDE_HOLDERS_GRAPH_URL
    active_holders_shares = get_feUSDe_active_holders_balance_at_block(
        FELIX_USDE_HOLDERS_GRAPH_URL, block_number
    )
    
    if not active_holders_shares:
        return {}
    
    # Convert to lists for easier batching
    user_addresses = list(active_holders_shares.keys())
    shares_list = list(active_holders_shares.values())
    total_users = len(user_addresses)
    
    print(f"Processing {total_users} users in {max_workers} threads with batch size {batch_size}")
    
    # Prepare batches
    batches = []
    for i in range(0, total_users, batch_size):
        batch_addresses = user_addresses[i:i + batch_size]
        batch_shares = shares_list[i:i + batch_size]
        batch_index = i // batch_size
        batches.append((batch_addresses, batch_shares, batch_index))
    
    # Process batches in parallel using ThreadPoolExecutor
    user_asset_balances = {}
    completed_batches = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batch processing tasks
        future_to_batch = {
            executor.submit(_process_batch, (batch_addresses, batch_shares), block_number, batch_index): batch_index
            for batch_addresses, batch_shares, batch_index in batches
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_batch):
            batch_index = future_to_batch[future]
            try:
                _, batch_results = future.result()
                user_asset_balances.update(batch_results)
                completed_batches += 1
                print(f"Progress: {completed_batches}/{len(batches)} batches completed")
            except Exception as e:
                print(f"Batch {batch_index + 1} generated an exception: {e}")
    
    print(f"Completed processing {len(user_asset_balances)} users across {completed_batches} batches")
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
