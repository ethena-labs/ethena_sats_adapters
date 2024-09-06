from utils.web3_utils import (
    W3_BY_CHAIN,
    fetch_events_logs_with_retry,
)
from web3.contract import Contract
from utils.web3_utils import call_with_retry
import logging
from constants.chains import Chain
from constants.integration_ids import IntegrationID
from constants.allstake import ALLSTAKE_STRATEGIES
from models.integration import Integration


SHARES_OFFSET = 1000
BALANCE_OFFSET = 1000

def get_underlying_balance(user: str, block: int, underlying: Contract, strategy: Contract):
    """
    User's underlying token balance = underlying token balance of strategy contract * strategy.balanceOf(user) / strategy.totalSupply()
    """

    total_underlying_balance = call_with_retry(underlying.functions.balanceOf(strategy.address), block) + BALANCE_OFFSET
    total_shares = call_with_retry(strategy.functions.totalSupply(), block) + SHARES_OFFSET
    user_shares = call_with_retry(strategy.functions.balanceOf(user), block)
    return user_shares * total_underlying_balance / total_shares

def get_strategy_users(start_block: int, page_size: int, strategy: Contract, chain: Chain):
    """
    Gets all participants that have ever interacted with the strategy by fetching all transfer events.
    """
    all_users = set()

    target_block = W3_BY_CHAIN[chain]["w3"].eth.get_block_number()

    while start_block < target_block:
        to_block = min(start_block + page_size, target_block)
        event_label = f"Getting participants from {start_block} to {to_block}"

        transfers = fetch_events_logs_with_retry(
            event_label,
            strategy.events.Transfer(),
            start_block,
            to_block,
        )
        print(event_label, ": found", len(transfers), "transfers")
        for transfer in transfers:
            all_users.add(transfer["args"]["to"])
        start_block += page_size
    return all_users


class AllstakeIntegration(Integration):
    def __init__(self, integration_id: IntegrationID):
        self.strategy_info = ALLSTAKE_STRATEGIES[integration_id]

        print(self.strategy_info)

        super().__init__(
            integration_id,
            self.strategy_info["start"],
            self.strategy_info["chain"],
            None,
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        return get_underlying_balance(
            user,
            block,
            self.strategy_info["underlying"],
            self.strategy_info["strategy"],
        )

    def get_participants(self) -> list:
        logging.info(f"[{self.integration_id.get_description()}] Getting participants...")
        self.participants = get_strategy_users(
            self.start_block,
            self.strategy_info["page_size"],
            self.strategy_info["strategy"],
            self.chain,
        )

        return self.participants