import logging
import json
from copy import deepcopy
from typing import Dict, List, Optional, Set, TypedDict, Any
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract import Contract
from constants.chains import Chain
from constants.example_integrations import PAGINATION_SIZE
from constants.summary_columns import SummaryColumn
from constants.strata import (
    STRATA_MAINNET
)
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import (
    ETH_NODE_URL,
    call_with_retry,
    fetch_events_logs_with_retry,
)

ERC4626_ABI = json.loads(open("abi/ERC4626_abi.json").read())

class StrataJrUSDeIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID = IntegrationID.STRATA_MONEY_JUNIOR,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = [SummaryColumn.STRATA_MONEY_JUNIOR],
        reward_multiplier: int = 5,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
        rpc = ETH_NODE_URL,
        strata = STRATA_MAINNET,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=min(c["block"] for c in strata["tranches"]),
            chain=chain,
            summary_cols=summary_cols,
            reward_multiplier=reward_multiplier,
            excluded_addresses=excluded_addresses
        )
        # Initialize Web3 provider - use ETH_NODE_URL from environment variables
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        if not self.w3.is_connected():
            logging.error(f"Failed to connect to RPC at {ETH_NODE_URL}")
            raise ConnectionError(f"Could not connect to Ethereum RPC at {ETH_NODE_URL}")
        logging.info(f"Connected to Ethereum RPC at {ETH_NODE_URL}")

        # Initialize tranche
        tranche = next((c for c in strata["tranches"] if c["name"] == "jrUSDe"), None)
        self.tranche = tranche
        self.contract_tranche: Contract  = self.w3.eth.contract(
            address=tranche["address"],
            abi=ERC4626_ABI,
        )
        self.contract_sUSDe: Contract  = self.w3.eth.contract(
            address=strata["sUSDe"]["address"],
            abi=ERC4626_ABI,
        )


    def get_balance (self, user: str, block: int) -> float:
        balance = call_with_retry(
            self.contract_tranche.functions.balanceOf(Web3.to_checksum_address(user)), block = block
        )
        tranchePps = self.get_tranche_pps(block)
        sUSDe_balance = balance * tranchePps
        return round(sUSDe_balance / 10**18, 6)

    def get_tranche_pps(self, block: int) -> float:
        """
        Calculate price per share (in sUSDe) for a given tranche and block and cache result.
        1. Calculate pps in USDe
        2. Convert USDe pps to sUSDe
        3. Cache
        """

        # Initialize cache dict once
        if not hasattr(self, "_pps_cache"):
            self._pps_cache: dict[int, float] = {}

        # Return cached PPS if already calculated for this contract and block
        if block in self._pps_cache:
            return self._pps_cache[block]

        pps_tranche_in_usde = self.get_erc4626_pps(self.contract_tranche, block)
        pps_susde_in_usde = self.get_erc4626_pps(self.contract_sUSDe, block)
        pps = pps_tranche_in_usde / pps_susde_in_usde

        # Cache result
        self._pps_cache[block] = pps
        return pps

    def get_erc4626_pps(self, erc4626: Contract, block: int) -> float:
        """
        Generic method to calculate price per share for ERC4626 contracts.
        """
        total_assets = erc4626.functions.totalAssets().call(block_identifier=block)
        total_supply = erc4626.functions.totalSupply().call(block_identifier=block)
        pps = float(total_assets) / float(total_supply)
        return pps

    def convert_block_balances_to_assets(
        self, block_balances: Dict[ChecksumAddress, float], block: int
    ) -> Dict[ChecksumAddress, float]:
        """
        Convert Tranche shares to sUSDe assets for a given block.
        """
        pps = self.get_tranche_pps(block)
        balances_assets = {addr: value * pps for addr, value in block_balances.items()}
        return balances_assets

    def convert_block_balances_to_shares(
        self, block_balances: Dict[ChecksumAddress, float], block: int
    ) -> Dict[ChecksumAddress, float]:
        """
        Convert sUSDe assets to Tranche shares for a given block.
        """
        pps = self.get_tranche_pps(block)
        balances_shares = {addr: value / pps for addr, value in block_balances.items()}
        return balances_shares


    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        """
        Get user balances for specified blocks, using cached data when available.

        This method returns and caches the balances in sUSDe. Whenever cached data is passed,
        we convert it to tranche shares for that block and process new transfer events.
        Afterwards, the balances dictionary is converted back to sUSDe balances.

        Args:
            cached_data: Dictionary mapping block numbers to user balances at that block
            blocks: List of block numbers to get balances for

        Returns:
            Dictionary mapping block numbers to user balances at that block
        """
        logging.info(f"[{self.tranche['name']}] Getting block balances")

        new_block_data: Dict[int, Dict[ChecksumAddress, float]] = {}
        if not blocks:
            return new_block_data

        blocks = sorted(blocks)


        cache_copy: Dict[int, Dict[ChecksumAddress, float]] = deepcopy(cached_data)
        # convert cached data to tokens
        cache_copy = {block: self.convert_block_balances_to_shares(balances, block) for block, balances in cache_copy.items()}

        for block in blocks:
            # find the closest prev block in the data
            # list keys parsed as ints and in descending order
            sorted_existing_blocks = sorted(
                cache_copy,
                reverse=True,
            )
            # loop through the sorted blocks and find the closest previous block
            prev_block = self.start_block
            start = prev_block
            balances = {}
            for existing_block in sorted_existing_blocks:
                if existing_block < block:
                    prev_block = existing_block
                    start = existing_block + 1
                    balances = deepcopy(cache_copy[prev_block])
                    break
            # parse transfer events since and update balances
            while start <= block:
                to_block = min(start + PAGINATION_SIZE, block)
                transfers = fetch_events_logs_with_retry(
                    "jrUSDe Token transfers",
                    self.contract_tranche.events.Transfer(),
                    start,
                    to_block,
                )
                for transfer in transfers:
                    sender = transfer["args"]["from"]
                    recipient = transfer["args"]["to"]
                    if recipient not in balances:
                        balances[recipient] = 0
                    if sender not in balances:
                        balances[sender] = 0

                    amount_tranche = transfer["args"]["value"]
                    amount = round(amount_tranche / 10**18, 6)
                    balances[sender] -= min(amount, balances[sender])
                    balances[recipient] += amount

                start = to_block + 1

            balances.pop('0x0000000000000000000000000000000000000000', None)
            new_block_data[block] = self.convert_block_balances_to_assets(balances, block)
            cache_copy[block] = balances
        return new_block_data



if __name__ == "__main__":
    example_integration = StrataJrUSDeIntegration()

    BLOCK_1 = 23534701
    BLOCK_2 = 23548724

    current_block = example_integration.w3.eth.get_block_number()
    # Without cached data
    without_cached_data_output = example_integration.get_block_balances(
        cached_data={}, blocks=[ BLOCK_1 ]
    )

    print("=" * 120)
    print("Run without cached data", without_cached_data_output)
    print("=" * 120)

    # With cached data, using the previous output so there is no need
    # to fetch the previous blocks again
    with_cached_data_output = example_integration.get_block_balances(
        cached_data=without_cached_data_output, blocks=[BLOCK_2]
    )
    print("Run with cached data", with_cached_data_output)
    print("=" * 120)

    # Fetch balance in one go up to BLOCK_2 and check the balance for user is the same
    integration_1 = StrataJrUSDeIntegration()
    balances = integration_1.get_block_balances(
        cached_data={}, blocks=[ BLOCK_2 ]
    )

    user = "0x5071479276AD65a5D7E04230C226c25e2522891a"
    print("One-Go-Fetch", balances[BLOCK_2][user])
    print("Cache-Fetch", with_cached_data_output[BLOCK_2][user])
    print("Balance-Fetch", integration_1.get_balance(user, block=BLOCK_2))
