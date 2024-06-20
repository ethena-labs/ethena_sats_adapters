
from abc import ABC, abstractmethod

from chains import Chain
from integrations.integration_ids import IntegrationID
from summary_columns import SummaryColumn


class Integration(ABC):

    @abstractmethod
    def get_balance(self, user: str, block: int) -> float:
        pass

    @abstractmethod
    def get_participants(self) -> list:
        pass

    def get_id(self) -> IntegrationID:
        return self.integration_id

    def get_description(self) -> str:
        return self.integration_id.get_description()

    def get_col_name(self) -> str:
        return self.integration_id.get_column_name()

    def get_chain(self) -> Chain:
        return self.chain

    def get_summary_cols(self) -> list[SummaryColumn]:
        return self.summary_cols

    def get_reward_multiplier(self) -> int:
        if self.reward_multiplier_func is not None:
            return self.reward_multiplier_func(self.start_block)
        return self.reward_multiplier

    def get_balance_multiplier(self) -> int:
        return self.balance_multiplier

    def get_start_block(self) -> int:
        return self.start_block

    def get_end_block(self) -> int:
        if self.end_block is None:
            return 2**31 - 1  # if no end block is specified, return the maximum possible block number
        return self.end_block

    def is_user_a_participant(self, user: str) -> bool:
        if self.participants is None:
            self.get_participants()
        return user in self.participants

