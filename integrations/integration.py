from abc import ABC
from typing import Dict, List, Optional, Set
from eth_typing import ChecksumAddress

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.integration_ids import IntegrationID


class Integration(ABC):

    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        chain: Chain,
        summary_cols: list[SummaryColumn] | None = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block: Optional[int] = None,
        reward_multiplier_func=None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func=None,
    ):
        self.integration_id = integration_id
        self.start_block = start_block
        self.end_block = end_block
        self.participants: set[str] = set()
        self.chain = chain
        self.summary_cols = summary_cols
        self.reward_multiplier = reward_multiplier
        self.balance_multiplier = balance_multiplier
        self.excluded_addresses = excluded_addresses
        self.reward_multiplier_func = reward_multiplier_func
        self.ethereal_multiplier = ethereal_multiplier
        self.ethereal_multiplier_func = ethereal_multiplier_func

    def get_balance(self, user: str, block: int) -> float:
        raise NotImplementedError

    def get_participants(
        self,
        blocks: Optional[List[int]],
    ) -> Set[str]:
        raise NotImplementedError

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        raise NotImplementedError

    def get_l2_block_balances(
        self,
        cached_data: Dict[int, Dict[str, float]],
        blocks: List[int],
    ) -> Dict[int, Dict[str, float]]:
        raise NotImplementedError
