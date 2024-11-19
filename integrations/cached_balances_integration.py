from typing import Callable, Dict, List, Optional, Set
from eth_typing import ChecksumAddress
from constants.summary_columns import SummaryColumn
from constants.chains import Chain
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID as IntID


class CachedBalancesIntegration(Integration):
    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
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

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        raise NotImplementedError
