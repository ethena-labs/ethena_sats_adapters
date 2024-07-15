import logging
from constants.integration_ids import IntegrationID
from models.integration import Integration
import utils.pendle as pendle

from eth_typing import ChecksumAddress
from web3.contract import Contract

from typing import Callable, List
from constants.chains import Chain  
from utils.slack import slack_message
from constants.summary_columns import SummaryColumn
from utils.web3_utils import call_with_retry


class PendleYTIntegration(Integration):

    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        yt_contract: Contract,
        get_participants_func: Callable[
            [[ChecksumAddress]], list  # type: ignore
        ] = pendle.get_pendle_participants_v3,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: list[SummaryColumn] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: list[str] = None,
        end_block: int = None,
        reward_multiplier_func: Callable[[int], int] = None,
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            summary_cols,
            reward_multiplier,
            balance_multiplier,
            excluded_addresses,
            end_block,
            reward_multiplier_func,
        )
        self.yt_contract = yt_contract
        self.summary_cols = (
            [SummaryColumn.PENDLE_SHARDS] if summary_cols is None else summary_cols
        )
        self.get_participants_func = get_participants_func

    def get_balance(self, user: str, block: int) -> float:
        if (block < self.start_block) or (
            self.end_block is not None and block > self.end_block
        ):
            return 0
        try:
            logging.info(
                f"[{self.get_description()}] Getting balance for {user} at block {block}"
            )
            # protect against silent rpc errors leading to large erroneous values
            res = call_with_retry(self.yt_contract.functions.balanceOf(user), block)
            if not isinstance(res, (int, float)):
                return 0
            return round(res / 10**18, 4)
        except Exception as e:
            err_msg = (
                f"[{self.get_description()}] Issue getting balance for {user} at block {block}. Returning 0. "
                f"Exception: {e}"
            )
            logging.error(err_msg)
            slack_message(err_msg)
            return 0

    def get_participants(self, _: List[int] = None) -> list:
        logging.info(f"[{self.get_description()}] Getting participants...")
        new_participants = self.get_participants_func(
            [self.yt_contract.address], self.get_new_blocks_start()
        )
        logging.info(
            f"[{self.get_description()}] Found {len(new_participants)} participants"
        )
        return new_participants
