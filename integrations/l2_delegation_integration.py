from typing import Callable, Dict, List, Optional, Set
from eth_typing import ChecksumAddress

from constants.summary_columns import SummaryColumn
from constants.chains import Chain
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID as IntID


"""
This class serves as an example implementation for L2 delegation integration.
The methods defined here are used in our backend to handle layer 2 delegation data.
Actual implementation details have been removed for security purposes.
"""


class L2DelegationIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        chain: Chain = Chain.SOLANA,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 20,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block: Optional[int] = None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func: Optional[Callable[[int, str], int]] = None,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            balance_multiplier=balance_multiplier,
            excluded_addresses=excluded_addresses,
            end_block=end_block,
            ethereal_multiplier=ethereal_multiplier,
            ethereal_multiplier_func=ethereal_multiplier_func,
        )

    def get_l2_block_balances(
        self,
        cached_data: Dict[int, Dict[str, float]],
        blocks: List[int],
    ) -> Dict[int, Dict[str, float]]:
        raise NotImplementedError

    def get_participants_data(self, block: int) -> Dict[str, float]:
        raise NotImplementedError
