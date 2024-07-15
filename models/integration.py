from abc import ABC, abstractmethod
from typing import List

from constants.chains import Chain
from constants.integration_ids import IntegrationID
from constants.summary_columns import SummaryColumn


class Integration(ABC):

    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain,
        summary_cols: list[SummaryColumn],
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: List[str] = None,
        end_block: int = None,
        reward_multiplier_func=None,
    ):
        self.integration_id = integration_id
        self.start_block = start_block
        self.end_block = end_block
        self.participants = None
        self.participants_cutoff_block: int = None
        self.chain = chain
        self.summary_cols = summary_cols
        self.reward_multiplier = reward_multiplier
        self.balance_multiplier = balance_multiplier
        self.excluded_addresses = excluded_addresses
        self.reward_multiplier_func = reward_multiplier_func

    @abstractmethod
    def get_balance(self, user: str, block: int) -> float:
        pass

    @abstractmethod
    def get_participants(self, blocks: List[int]) -> List[str] | None:
        pass

    def get_description(self) -> str:
        return self.integration_id.get_description()

    def get_new_blocks_start(self) -> int:
        return (
            self.participants_cutoff_block
            if self.participants_cutoff_block is not None
            and self.participants_cutoff_block > self.start_block
            else self.start_block
        )
