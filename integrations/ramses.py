from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.ramses import RAMSES_DEPLOYMENT_BLOCK,RAMSES_GAUGE_ADDRESS,RAMSES_POOL_ADDRESS,ARBITRUM_USDE_TOKEN_ADDRESS
from constants.summary_columns import SummaryColumn
from utils.ramses import pool, gauge
from utils.web3_utils import w3_arb, fetch_events_logs_with_retry, call_with_retry
from web3 import Web3
import math

class Ramses(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.RAMSES_USDE_LP,
            RAMSES_DEPLOYMENT_BLOCK,
            Chain.ARBITRUM,
            [SummaryColumn.RAMSES_SHARDS],
            20,
            1,
        )

    def get_underlying_balances(self, user: str, block: int) -> tuple:
        user_balance = self.get_balance(user, block)
        total_supply = self.get_total_supply(block)
        
        if total_supply == 0:
            return 0, 0

        reserves = call_with_retry(
            pool.functions.getReserves(),
            block,
        )
        
        token0_balance = (user_balance / total_supply) * reserves[0] / 1e18
        token1_balance = (user_balance / total_supply) * reserves[1] / 1e18
        
        return token0_balance, token1_balance

    def get_balance(self, user: str, block: int) -> float:
        try:
            user_balance = call_with_retry(
                gauge.functions.balanceOf(user),
                block,
            )
            total_supply = call_with_retry(
                gauge.functions.totalSupply(),
                block
            )
        
            if total_supply == 0:
                return 0, 0

            reserves = call_with_retry(
                pool.functions.getReserves(),
                block,
            )
            
            token0_balance = (user_balance / total_supply) * reserves[0] / 1e18 #USDe 18decimals
            token1_balance = (user_balance / total_supply) * reserves[1] / 1e18 #USDx 18decimals
            
            return token0_balance

        except ValueError as e:
            print(f"Error getting balance at block {block}: {e}")
            return 0
    


    def get_participants(self) -> list:
        page_size = 999
        start_block = RAMSES_DEPLOYMENT_BLOCK
        target_block = w3_arb.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            print(f"Fetching events from block {start_block} to {start_block + page_size}")
            to_block = min(start_block + page_size, target_block)
            try:
                deposit_events = fetch_events_logs_with_retry(
                    f"USDe pool Deposit events from {start_block} to {to_block}",
                    gauge.events.Deposit(),
                    start_block,
                    to_block,
                )
                
                for event in deposit_events:
                    user_address = event['args']['from']
                    print(f"User address: {user_address}")
                    all_users.add(user_address)

            except Exception as e:
                print(f"Error fetching events from block {start_block} to {to_block}: {e}")
            
            start_block += page_size

        self.participants = list(all_users)
        return self.participants
    
if __name__ == "__main__":
    ramses = Ramses()
    #latest_block = w3_arb.eth.get_block_number()
    #test_block = latest_block - 100
    #print(f"Testing with block number: {test_block}")
    
    #test_address = Web3.to_checksum_address("0xa1FC03e69e031AE9682b6e1B2c9669A33dE39b09")
    #print(f"Balance for {test_address}: {ramses.get_balance(test_address, test_block)}")
    
    #participants = ramses.get_participants()
    #print(f"Number of participants: {len(participants)}")
    #if participants:
    #    print(f"Balance for first participant: {ramses.get_balance(participants[0], test_block)}")
