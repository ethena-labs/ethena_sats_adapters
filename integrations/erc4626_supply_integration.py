import json
import logging
from copy import deepcopy
from dataclasses import dataclass
from eth_typing import ChecksumAddress
from typing import Callable, Dict, List, Optional, Set
from web3 import Web3
from web3.contract import Contract

from constants.chains import Chain
from constants.example_integrations import PAGINATION_SIZE
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import fetch_events_logs_with_retry, w3

with open("abi/ERC4626_abi.json") as f:
    ERC4626_ABI = json.load(f)


class Erc4626SupplyIntegration(CachedBalancesIntegration):
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
        self.vault = self.get_vault_config(integration_id)
        self.vault_contract = self.create_vault_contract(self.vault.address)
        self.share_rates_cache: Dict[int, float] = {}

        super().__init__(
            integration_id=integration_id,
            start_block=self.vault.start_block,
            chain=self.vault.chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            balance_multiplier=balance_multiplier,
            excluded_addresses=excluded_addresses,
            end_block=end_block,
            ethereal_multiplier=ethereal_multiplier,
            ethereal_multiplier_func=ethereal_multiplier_func,
        )

    def get_vault_config(self, integration_id: IntegrationID) -> "VaultConfig":
        vault = VAULT_BY_INTEGRATION.get(integration_id)
        if not vault:
            raise ValueError(f"Vault not found for integration {integration_id}")
        return vault

    def create_vault_contract(self, address: str) -> Contract:
        return w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=ERC4626_ABI,
        )

    def get_share_rate(self, block: int) -> float:
        if block in self.share_rates_cache:
            return self.share_rates_cache[block]

        logging.info(f"Getting share rate for vault at block {block}")
        total_supply = self.vault_contract.functions.totalSupply().call(
            block_identifier=block
        )
        total_assets = self.vault_contract.functions.totalAssets().call(
            block_identifier=block
        )
        share_rate = self.calculate_share_rate(total_assets, total_supply)

        self.share_rates_cache[block] = share_rate
        return share_rate

    def calculate_share_rate(self, total_assets: int, total_supply: int) -> float:
        if total_supply == 0:
            return 0
        return (total_assets / 10**self.vault.asset_decimals) / (
            total_supply / 10**self.vault.share_decimals
        )

    def get_closest_balances_snapshot(
        self, cache: Dict[int, Dict[ChecksumAddress, float]], block: int
    ) -> tuple[int, Dict[ChecksumAddress, float]]:
        closest_block = max(
            (cached_block for cached_block in cache if cached_block <= block),
            default=self.start_block,
        )
        return closest_block, cache.get(closest_block, {})

    def asset_bals_to_share_bals(
        self, asset_bals: Dict[ChecksumAddress, float], share_rate: float
    ) -> Dict[ChecksumAddress, float]:
        return {
            addr: max(balance / share_rate, 0) if share_rate != 0 else 0
            for addr, balance in asset_bals.items()
        }

    def share_bals_to_asset_bals(
        self, share_bals: Dict[ChecksumAddress, float], share_rate: float
    ) -> Dict[ChecksumAddress, float]:
        return {
            addr: max(balance * share_rate, 0) for addr, balance in share_bals.items()
        }

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
            current_share_rate = self.get_share_rate(block)
            prev_block, prev_asset_bals = self.get_closest_balances_snapshot(
                cache_copy, block
            )
            prev_share_rate = self.get_share_rate(prev_block)
            share_bals = self.asset_bals_to_share_bals(prev_asset_bals, prev_share_rate)

            self.update_balances_with_transfers(share_bals, prev_block, block)
            new_block_data[block] = cache_copy[block] = self.share_bals_to_asset_bals(
                share_bals, current_share_rate
            )

        return new_block_data

    def update_balances_with_transfers(
        self, share_bals: Dict[ChecksumAddress, float], from_block: int, to_block: int
    ) -> None:
        while from_block <= to_block:
            end_block = min(from_block + PAGINATION_SIZE, to_block)
            transfers = fetch_events_logs_with_retry(
                "Vault shares transfers",
                self.vault_contract.events.Transfer(),
                from_block,
                end_block,
            )

            for transfer in transfers:
                recipient = transfer["args"]["to"]
                sender = transfer["args"]["from"]
                value = transfer["args"]["value"] / 10**self.vault.share_decimals

                share_bals[recipient] = share_bals.get(recipient, 0) + round(value, 4)
                share_bals[sender] = share_bals.get(sender, 0) - round(value, 4)

            from_block = end_block + 1


@dataclass
class VaultConfig:
    chain: Chain
    start_block: int
    address: str
    asset_decimals: int = 18
    share_decimals: int = 18


VAULT_BY_INTEGRATION: Dict[IntegrationID, VaultConfig] = {
    IntegrationID.APOSTRO_MORPHO_USDE_VAULT: VaultConfig(
        chain=Chain.ETHEREUM,
        start_block=22076668,
        address="0x4EDfaB296F8Eb15aC0907CF9eCb7079b1679Da57",
    ),
}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_vault_integration = Erc4626SupplyIntegration(
        integration_id=IntegrationID.APOSTRO_MORPHO_USDE_VAULT,
        summary_cols=[SummaryColumn.APOSTRO_MORPHO_PTS],
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
    )

    cache = test_vault_integration.get_block_balances(
        cached_data={}, blocks=[22076668, 22076669, 22076670]
    )
    print(cache)

    print(
        test_vault_integration.get_block_balances(
            cached_data=cache,
            blocks=[22076670, 22078670, 22080670, 22082670, 22084670, 22087605],
        )
    )
