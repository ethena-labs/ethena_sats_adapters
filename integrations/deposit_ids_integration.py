from typing import Dict, List, Optional, Set

from eth_typing import ChecksumAddress
from constants.summary_columns import SummaryColumn
from constants.chains import Chain
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID as IntID


class DepositIdsIntegration(Integration):
    """
    Some integrations require a deposit or token ID only obtainable from deposit events to get balances.
    We approach this by storing the deposit IDs on DB and overriding fetch_block_data.
    """

    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            balance_multiplier=1,
            excluded_addresses=excluded_addresses,
        )

    def fetch_participants(
        self, cache: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Set[ChecksumAddress]:
        """Override fetch_participants to handle deposit IDs."""
        raise NotImplementedError

    def get_deposit_ids_balances(
        self, deposit_ids: Set[int], user: ChecksumAddress, block: int
    ) -> float:
        raise NotImplementedError

    def get_participants_with_deposit_ids(
        self, blocks: List[int], cache: Optional[Dict[ChecksumAddress, Set[int]]] = None
    ) -> Dict[ChecksumAddress, Set[int]]:
        raise NotImplementedError
