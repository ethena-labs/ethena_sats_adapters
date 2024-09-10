from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.ramses import RAMSES_DEPLOYMENT_BLOCK, RAMSES_NFP_MANAGER_ADDRESS, RAMSES_POOL_ADDRESS, ARBITRUM_USDE_TOKEN_ADDRESS
from constants.summary_columns import SummaryColumn
from utils.ramses import nfp_manager, pool
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

    def calculate_sqrt_price(self, tick):
        return math.sqrt(1.0001**tick) * (2**96)

    def calculate_token_amounts(self, liquidity, current_tick, lower_tick, upper_tick, sqrt_price_x96, decimals0, decimals1):
        sqrt_price_current = sqrt_price_x96 / (2**96)
        sqrt_price_lower = self.calculate_sqrt_price(lower_tick) / (2**96)
        sqrt_price_upper = self.calculate_sqrt_price(upper_tick) / (2**96)

        if current_tick < lower_tick:
            amount0 = liquidity * (1 / sqrt_price_lower - 1 / sqrt_price_upper)
            amount1 = 0
        elif current_tick < upper_tick:
            amount0 = liquidity * (1 / sqrt_price_current - 1 / sqrt_price_upper)
            amount1 = liquidity * (sqrt_price_current - sqrt_price_lower)
        else:
            amount0 = 0
            amount1 = liquidity * (sqrt_price_upper - sqrt_price_lower)

        amount0_adjusted = amount0 / (10**decimals0)
        amount1_adjusted = amount1 / (10**decimals1)

        return max(amount0_adjusted, 0), max(amount1_adjusted, 0)

    def get_balance(self, user: str, block: int) -> float:
        # get pool current tick
        current_tick = call_with_retry(
            pool.functions.slot0(),
            block,
        )

        sqrtPriceX96 = current_tick[0]
        tick = current_tick[1]
        
        balance = call_with_retry(
            nfp_manager.functions.balanceOf(user),
            block,
        )

        print(f"User NFT balance: {balance}")

        total_balance = 0

        for i in range(balance):
            tokenId = call_with_retry(
                nfp_manager.functions.tokenOfOwnerByIndex(user, i),
                block,
            )

            position_info = call_with_retry(
                nfp_manager.functions.positions(tokenId),
                block,
            )
            print(f"Position info: {position_info}")
            token0 = position_info[2]
            token1 = position_info[3]
            tickLower = position_info[5]
            tickUpper = position_info[6]
            liquidity = position_info[7]

            amount0, amount1 = self.calculate_token_amounts(
                liquidity, tick, tickLower, tickUpper, sqrtPriceX96, 18, 18
            )

            if token0 == ARBITRUM_USDE_TOKEN_ADDRESS:
                print(f"Amount0 (USDe): {amount0}")
                print(f"Amount1: {amount1}")
                total_balance += amount0
            elif token1 == ARBITRUM_USDE_TOKEN_ADDRESS:
                print(f"Amount0: {amount0}")
                print(f"Amount1 (USDe): {amount1}")
                total_balance += amount1

        return total_balance

    def get_participants(self) -> list:
        page_size = 999
        start_block = RAMSES_DEPLOYMENT_BLOCK
        target_block = w3_arb.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            try:
                mint_events = fetch_events_logs_with_retry(
                    f"USDe pool Mint events from {start_block} to {to_block}",
                    pool.events.Mint(),
                    start_block,
                    to_block,
                )
                print(f"Fetched {len(mint_events)} Mint events")
                
                for event in mint_events:
                    tx_hash = event['transactionHash']
                    tx = w3_arb.eth.get_transaction(tx_hash)
                    user_address = tx['from']
                    all_users.add(user_address)

            except Exception as e:
                print(f"Error fetching events from block {start_block} to {to_block}: {e}")
            
            start_block += page_size

        self.participants = list(all_users)
        return self.participants
    
if __name__ == "__main__":
    ramses = Ramses()
    try:
        latest_block = w3_arb.eth.get_block_number()
        test_block = latest_block - 100
        print(f"Testing with block number: {test_block}")
        
        test_address = Web3.to_checksum_address("0x38564BAa609b6B9df4A0341A2589489aa3F870ee")
        balance = ramses.get_balance(test_address, test_block)
        print(f"Balance for {test_address}: {balance}")
        
        participants = ramses.get_participants()
        print(f"Number of participants: {len(participants)}")
        if participants:
            first_participant_balance = ramses.get_balance(participants[0], test_block)
            print(f"Balance for first participant: {first_participant_balance}")
    except Exception as e:
        print(f"An error occurred: {e}")
