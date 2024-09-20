import requests

from web3 import Web3
from web3.contract import Contract
from utils.web3_utils import call_with_retry

def get_effective_balance(user: str, block: int, collateral_address: str, r_token_contract: Contract, lending_pool: Contract):
    """
    User's effective ethena integration token balance = scaledBalanceOf(user) * liquidityIndex

    """
    user_checksum  = Web3.to_checksum_address(user)

    user_scaled_balance = call_with_retry(r_token_contract.functions.scaledBalanceOf(user_checksum), block)
    reserve_data = call_with_retry(lending_pool.functions.getReserveData(collateral_address), block)
    usde_liquidity_index = reserve_data[1]
    return (user_scaled_balance * usde_liquidity_index) / (10 ** 45) # 10 ** (27 + 18)

def get_radiant_lenders(graph_url: str, collateral_address: str):
    url = graph_url
    skip = 0
    all_positions = []

    while True:
        query = """
        {
            positions(first: 1000, skip: %s, where :{ side: COLLATERAL, asset: "%s" }) {
                account {
                    id
                }
            }
        }
        """ % (skip, collateral_address)

        response = requests.post(url, json={'query': query})


        if response.status_code == 200:
            data = response.json()

            positions = data['data']['positions']

            if not positions:
                break
            filtered_positions = [position['account']['id'] for position in positions if position['account']['id']
                                    != '0x0000000000000000000000000000000000000000']
            all_positions.extend(filtered_positions)
            skip += 1000
        else:
            raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

    return list(set(all_positions))
