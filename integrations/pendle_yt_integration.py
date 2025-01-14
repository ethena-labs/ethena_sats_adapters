from typing import Callable, List, Optional
import logging

from eth_typing import ChecksumAddress
from web3.contract import Contract

from constants.chains import Chain
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from constants.summary_columns import SummaryColumn
from utils.pendle import get_pendle_participants_v3
from utils.web3_utils import call_with_retry


class PendleYTIntegration(Integration):

    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        yt_contract: Contract,
        get_participants_func: Callable[
            [list[ChecksumAddress]], set[str]
        ] = get_pendle_participants_v3,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        end_block: int | None = None,
        reward_multiplier_func: Callable[[int], int] | None = None,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            balance_multiplier=balance_multiplier,
            end_block=end_block,
            reward_multiplier_func=reward_multiplier_func,
        )
        self.yt_contract = yt_contract
        self.summary_cols = (
            [SummaryColumn.PENDLE_SHARDS] if summary_cols is None else summary_cols
        )
        self.get_participants_func = get_participants_func

    def get_balance(self, user: str, block: int) -> float:
        logging.info(f"[Pendle YT] Getting balance for {user} at block {block}")
        # protect against silent rpc errors leading to large erroneous values
        res = call_with_retry(self.yt_contract.functions.balanceOf(user), block)
        if not isinstance(res, (int, float)):
            return 0
        return round(res / 10**18, 4)

    def get_participants(self, blocks: list[int] | None = None) -> set[str]:
        if self.participants is not None:
            return self.participants

        logging.info("[Pendle YT] Getting participants...")
        self.participants = self.get_participants_func([self.yt_contract.address])
        logging.info(
            f"[{self.get_description()}] Found {len(self.participants)} participants"
        )
        return self.participants
