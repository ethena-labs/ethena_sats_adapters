import logging
import requests
from typing import Callable, Dict, List, Optional, Set

from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from constants.terminal import TERMMAX_API_URL
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.terminal import convert_to_decimals

class TerminalTermMaxIntegration(
    CachedBalancesIntegration
):
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

    def fetch_balances(self, block: int) -> Dict[ChecksumAddress, float]:
        data = requests.get(
            f"{TERMMAX_API_URL}/integrations/terminal/tusde_effective_balances",
            params={ "block_id": block }
        )

        if data.status_code != 200:
            logging.error(f"Failed to effective balances for block {block}")
            return {}

        accounts = data.json()["data"]["effective_balances"]

        balances = {}
        for account in accounts:
            balances[account["account_address"]] = convert_to_decimals(int(account["balance"]))

        return balances

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
        logging.info("Getting block data for Terminal Finance tUSDe on TermMax...")
        block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            logging.error("No blocks provided to get_block_balances")
            return block_data

        for target_block in sorted(blocks):
            block_data[target_block] = self.fetch_balances(target_block)

        return block_data

if __name__ == "__main__":
    integration = TerminalTermMaxIntegration(
        integration_id=IntegrationID.EXAMPLE,
        start_block=22000000,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=40000000,
    )

    data_output = integration.get_block_balances(
        cached_data={}, blocks=[22985000, 22987200]
    )

    assert data_output == {
        22985000: { 
            "0x03d96DC162Dc483B03ED56eF2884bBC8921F6C1A": 5.0,
            "0x53cfae9AF39Fa1eeD00D4402ed6cEAbB112a3724": 1000.0
        },
        22987200: { 
            "0xD6B34b1674792D9ed63baB92cB8D0518C257c18a": 1.0,
            "0x53cfae9AF39Fa1eeD00D4402ed6cEAbB112a3724": 1000.0,
            "0x03d96DC162Dc483B03ED56eF2884bBC8921F6C1A": 5.0
        },
    }

    print("Tests passed!")