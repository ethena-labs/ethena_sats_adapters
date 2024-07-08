from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.nuri import NURI_NFP_MANAGER_ADDRESS, NURI_POOL_ADDRESS, NURI_DEPLOYMENT_BLOCK, SCROLL_USDE_TOKEN_ADDRESS
from constants.summary_columns import SummaryColumn
from utils.nuri import nfp_manager, pool
from utils.web3_utils import w3_scroll, fetch_events_logs_with_retry, call_with_retry
from web3 import Web3
import math
class Nuri(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.NURI_USDE_LP,
            NURI_DEPLOYMENT_BLOCK,
            Chain.SCROLL,
            [SummaryColumn.NURI_SHARDS],
            20,
            1,
        )

    def calculate_sqrt_price(self, tick):
        return math.sqrt(1.0001**tick) * (2**96)

    def calculate_token_amounts(self, liquidity, current_tick, lower_tick, upper_tick, sqrt_price_x96, decimals0, decimals1):
        sqrt_price_current = sqrt_price_x96
        sqrt_price_lower = self.calculate_sqrt_price(lower_tick)
        sqrt_price_upper = self.calculate_sqrt_price(upper_tick)

        amount0 = liquidity * (sqrt_price_upper - sqrt_price_current) / (sqrt_price_current * sqrt_price_upper) * (2**96)
        amount1 = liquidity * (sqrt_price_current - sqrt_price_lower) / (2**96)

        amount0_adjusted = amount0 / (10**decimals0)
        amount1_adjusted = amount1 / (10**decimals1)

        return amount0_adjusted, amount1_adjusted

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

        positions = []

        for i in range(balance):
            tokenOfOwnerByIndex = call_with_retry(
                nfp_manager.functions.tokenOfOwnerByIndex(user, i),
                block,
            )

            positions.append(tokenOfOwnerByIndex)

        print(f"User positions: {positions}")

        total_balance = 0

        for position in positions:
            position_info = call_with_retry(
                nfp_manager.functions.positions(position),
                block,
            )
            print(f"Position info: {position_info}")
            token0 = position_info[2]
            token1 = position_info[3]
            tickLower = position_info[5]
            tickUpper = position_info[6]
            liquidity = position_info[7]

            if token0 == SCROLL_USDE_TOKEN_ADDRESS:
                # Calculate token amounts for this position
                amount0, amount1 = self.calculate_token_amounts(
                    liquidity, tick, tickLower, tickUpper, sqrtPriceX96, 18, 6  # Assuming USDe is 18 decimals and USDT is 6
                )

                # Assuming we want to sum up the USDe amounts
                total_balance += amount0

        return total_balance

    def get_participants(self) -> list:
        page_size = 999
        start_block = NURI_DEPLOYMENT_BLOCK
        target_block = w3_scroll.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            try:
                transfers = fetch_events_logs_with_retry(
                    f"Nuri users from {start_block} to {to_block}",
                    nfp_manager.events.Transfer(),
                    start_block,
                    to_block,
                )
                for transfer in transfers:
                    all_users.add(transfer["args"]["to"])
            except Exception as e:
                print(f"Error fetching transfers from block {start_block} to {to_block}: {e}")
            
            start_block = to_block + 1

        self.participants = list(all_users)
        return self.participants
    
if __name__ == "__main__":
    nuri = Nuri()
    #print(nuri.get_balance(Web3.to_checksum_address("0xCE29ECB0D2d8c8f0126ED923C50A35cFb0B613A8"), 7249275))
    #print(nuri.get_participants())
    #print(nuri.get_balance(nuri.participants[0], 7249275))
