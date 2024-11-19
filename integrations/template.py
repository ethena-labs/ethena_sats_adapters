from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3_typing import ChecksumAddress


class ProtocolNameIntegration(
    CachedBalancesIntegration
):  # TODO: Change ProtocolNameIntegration to the name of the protocol
    def __init__(
        self,
        integration_id: IntegrationID,
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
            integration_id,
            start_block,
            chain,
            summary_cols,
            reward_multiplier,
            balance_multiplier,
            excluded_addresses,
            end_block,
            ethereal_multiplier,
            ethereal_multiplier_func,
        )

    # TODO: Implement function that returns a dict of block numbers to a dict of user addresses to balances at that block
    # This function should be efficient and use onchain calls where possible
    # Example:
    # {
    #   20000000: {"0x123": 100, "0x456": 200},
    #   20000001: {"0x123": 101, "0x456": 201},
    #   20000002: {"0x123": 102, "0x456": 202},
    # }
    def get_block_balances(self, blocks: List[int]) -> Dict[int, Dict[str, float]]:
        pass


if __name__ == "__main__":
    # TODO: Write a simple test for the integration
    example_integration = ProtocolNameIntegration()
    print(example_integration.get_block_balances([20000000, 20000001, 20000002]))
