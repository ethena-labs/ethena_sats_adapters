from abc import ABC, abstractmethod

from constants.chains import Chain
from constants.integration_ids import IntegrationID
from constants.summary_columns import SummaryColumn
from constants.integration_token import Token


class Integration(ABC):

    def __init__(self, integration_id: IntegrationID, start_block: int, chain: Chain, summary_cols: list[SummaryColumn],
                 reward_multiplier: int = 1, balance_multiplier: int = 1, end_block: int = None,
                 reward_multiplier_func=None):
        self.integration_id = integration_id
        self.start_block = start_block
        self.end_block = end_block
        self.participants = None
        self.chain = chain
        self.summary_cols = summary_cols
        self.reward_multiplier = reward_multiplier
        self.balance_multiplier = balance_multiplier
        self.reward_multiplier_func = reward_multiplier_func

    @abstractmethod
    def get_balance(self, user: str, block: int) -> float:
        pass

    @abstractmethod
    def get_participants(self) -> list:
        pass

    def get_id(self) -> IntegrationID:
        return self.integration_id

    def get_token(self) -> Token:
        return self.integration_id.get_token()

    def get_description(self) -> str:
        return self.integration_id.get_description()

    def get_col_name(self) -> str:
        return self.integration_id.get_column_name()

    def get_chain(self) -> Chain:
        return self.chain

    def get_summary_cols(self) -> list[SummaryColumn]:
        return self.summary_cols

    def get_reward_multiplier(self, block: int) -> int:
        if self.reward_multiplier_func is not None:
            return self.reward_multiplier_func(block)
        return self.reward_multiplier

    def get_balance_multiplier(self) -> int:
        return self.balance_multiplier

    def get_start_block(self) -> int:
        return self.start_block

    def get_end_block(self) -> int:
        if self.end_block is None:
            return 2 ** 31 - 1  # if no end block is specified, return the maximum possible block number
        return self.end_block

    def is_user_a_participant(self, user: str) -> bool:
        if self.participants is None:
            self.get_participants()
        return user in self.participants
