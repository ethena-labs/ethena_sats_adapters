from typing import Callable, Dict, List, Optional, Set
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from web3 import Web3
from eth_typing import ChecksumAddress


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

    # TODO: Implement this function
    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """Get user balances for specified blocks, using cached data when available.

        Args:
            cached_data (Dict[int, Dict[ChecksumAddress, float]]): Dictionary mapping block numbers
                to user balances at that block. Used to avoid recomputing known balances.
                The inner dictionary maps user addresses to their token balance.
            blocks (List[int]): List of block numbers to get balances for.

        Returns:
            Dict[int, Dict[ChecksumAddress, float]]: Dictionary mapping block numbers to user balances,
                where each inner dictionary maps user addresses to their token balance
                at that block.
        """
        # TODO: Implement your logic here
        return {}


if __name__ == "__main__":
    # TODO: Write simple tests for the integration
    example_integration = ProtocolNameIntegration(
        integration_id=IntegrationID.EXAMPLE,
        start_block=20000000,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=40000000,
    )
    print(
        example_integration.get_block_balances(
            cached_data={}, blocks=[20000000, 20000001, 20000002]
        )
    )
    # Example output:
    # {
    #   20000000: {"0x123": 100, "0x456": 200},
    #   20000001: {"0x123": 101, "0x456": 201},
    #   20000002: {"0x123": 102, "0x456": 202},
    # }

    print(
        example_integration.get_block_balances(
            cached_data={
                20000000: {
                    Web3.to_checksum_address("0x123"): 100,
                    Web3.to_checksum_address("0x456"): 200,
                },
                20000001: {
                    Web3.to_checksum_address("0x123"): 101,
                    Web3.to_checksum_address("0x456"): 201,
                },
            },
            blocks=[20000002],
        )
    )
    # Example output:
    # {
    #   20000002: {"0x123": 102, "0x456": 202},
    # }
