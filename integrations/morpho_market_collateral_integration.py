import json
import logging
from copy import deepcopy
from dataclasses import dataclass
from eth_typing import ChecksumAddress
from typing import Callable, Dict, List, Optional, Set
from web3 import Web3
from web3.contract import Contract
from web3.contract.base_contract import BaseContractEvent

from constants.chains import Chain
from constants.example_integrations import PAGINATION_SIZE
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import fetch_events_logs_with_retry, w3

with open("abi/IMorpho.json") as f:
    MORPHO_ABI = json.load(f)

MORPHO_ADDRESS = Web3.to_checksum_address("0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb")


class MorphoMarketCollateralIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 1,
        balance_multiplier: int = 1,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        end_block: Optional[int] = None,
        ethereal_multiplier: int = 0,
        ethereal_multiplier_func: Optional[Callable[[int, str], int]] = None,
    ):
        self.market = self.get_market_config(integration_id)
        self.morpho_contract = self.initialize_morpho_contract()

        super().__init__(
            integration_id=integration_id,
            start_block=self.market.start_block,
            chain=self.market.chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            balance_multiplier=balance_multiplier,
            excluded_addresses=excluded_addresses,
            end_block=end_block,
            ethereal_multiplier=ethereal_multiplier,
            ethereal_multiplier_func=ethereal_multiplier_func,
        )

    def get_market_config(self, integration_id: IntegrationID) -> "MarketConfig":
        market = MARKET_BY_INTEGRATION.get(integration_id)
        if not market:
            raise ValueError(f"Market not found for integration {integration_id}")
        return market

    def initialize_morpho_contract(self) -> Contract:
        return w3.eth.contract(
            address=MORPHO_ADDRESS,
            abi=MORPHO_ABI,
        )

    def get_closest_balances_snapshot(
        self, cache: Dict[int, Dict[ChecksumAddress, float]], block: int
    ) -> tuple[int, Dict[ChecksumAddress, float]]:
        closest_block = max(
            (cached_block for cached_block in cache if cached_block <= block),
            default=self.start_block,
        )
        return closest_block, cache.get(closest_block, {})

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info("Getting block balances for vault")
        if not blocks:
            logging.error("No blocks provided to get_block_balances")
            return {}

        sorted_blocks = sorted(blocks)
        cache_copy = deepcopy(cached_data)
        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}

        for block in sorted_blocks:
            prev_block, prev_asset_bals = self.get_closest_balances_snapshot(
                cache_copy, block
            )
            bals = deepcopy(prev_asset_bals)

            self.update_balances_with_transfers(bals, prev_block, block)
            new_block_data[block] = cache_copy[block] = bals

        return new_block_data

    def update_balances_with_transfers(
        self, bals: Dict[ChecksumAddress, float], from_block: int, to_block: int
    ) -> None:
        while from_block <= to_block:
            end_block = min(from_block + PAGINATION_SIZE, to_block)

            supply_diffs = self.fetch_collateral_diffs(
                "Supply collateral events",
                self.morpho_contract.events.SupplyCollateral(),
                from_block,
                end_block,
            )
            withdraw_diffs = self.fetch_collateral_diffs(
                "Withdraw collateral events",
                self.morpho_contract.events.WithdrawCollateral(),
                from_block,
                end_block,
                -1,
            )
            liquidate_diffs = self.fetch_collateral_diffs(
                "Liquidate collateral events",
                self.morpho_contract.events.Liquidate(),
                from_block,
                end_block,
                -1,
                "borrower",
                "seizedAssets",
            )
            all_diffs = supply_diffs + withdraw_diffs + liquidate_diffs

            for account, diff in all_diffs:
                bals[account] = max(0, bals.get(account, 0) + round(diff, 4))

            from_block = end_block + 1

    def fetch_collateral_diffs(
        self,
        event_name: str,
        event: BaseContractEvent,
        from_block: int,
        end_block: int,
        multiplier: int = 1,
        account_field: str = "onBehalf",
        assets_field: str = "assets",
    ) -> List[tuple[str, float]]:
        return [
            (
                event["args"][account_field],
                multiplier
                * event["args"][assets_field]
                / 10**self.market.collateral_decimals,
            )
            for event in fetch_events_logs_with_retry(
                event_name,
                event,
                from_block,
                end_block,
                filter={"id": self.market.id},
            )
        ]


@dataclass
class MarketConfig:
    chain: Chain
    start_block: int
    id: str
    collateral_decimals: int = 18


MARKET_BY_INTEGRATION: Dict[IntegrationID, MarketConfig] = {
    IntegrationID.APOSTRO_MORPHO_EUSDE_COLLATERAL: MarketConfig(
        chain=Chain.ETHEREUM,
        start_block=22001220,
        id="0x140fe48783fe88d2a52b31705577d917628caaf74ff79865b39d4c2aa6c2fd3c",
    ),
}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_vault_integration = MorphoMarketCollateralIntegration(
        integration_id=IntegrationID.APOSTRO_MORPHO_EUSDE_COLLATERAL,
        summary_cols=[SummaryColumn.APOSTRO_MORPHO_PTS],
        reward_multiplier=30,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
    )

    cache = test_vault_integration.get_block_balances(
        cached_data={}, blocks=[22001220, 22003220, 22005220, 22007220]
    )
    print(cache)

    print(
        test_vault_integration.get_block_balances(
            cached_data=cache,
            blocks=[
                22001220,
                22011220,
                22021220,
                22031220,
                22041220,
                22051220,
                22061220,
                22071220,
                22087605,
            ],
        )
    )
