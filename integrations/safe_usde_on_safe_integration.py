import csv
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from eth_typing import ChecksumAddress
from web3 import Web3

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from integrations.cached_balances_integration import CachedBalancesIntegration
from integrations.integration_ids import IntegrationID
from utils.request_utils import requests_retry_session
from utils.web3_utils import (
    W3_BY_CHAIN,
    MULTICALL_ADDRESS_BY_CHAIN,
    fetch_events_logs_with_retry,
    multicall_by_address,
)

USDE_TOKEN_ADDRESS = Web3.to_checksum_address(
    "0x4c9EDD5852cd905f086C759E8383e09bff1E68B3"
)
USDE_DECIMALS = 18

SAFE_API_URL = "https://api.safe.global/tx-service/eth"
SAFE_API_KEY = os.getenv("SAFE_API_KEY", "")

SAFE_USDE_START_BLOCK = 24179079  # ~Jan 8, 2026 (placeholder, adjust as needed)
SAFE_USDE_END_BLOCK = 25179079    # ~Feb 7, 2026 (placeholder, adjust as needed)

PAGINATION_SIZE = 10000

SAFE_ADDRESSES_CSV = Path(__file__).parent.parent / "data" / "Token_Balance_Holdings_for_Safes_at_block_number.csv"

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
]


class SafeUSDeOnSafeIntegration(CachedBalancesIntegration):
    def __init__(
        self,
        integration_id: IntegrationID = IntegrationID.SAFE_USDE_ON_SAFE,
        start_block: int = SAFE_USDE_START_BLOCK,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: Optional[List[SummaryColumn]] = None,
        reward_multiplier: int = 20,
        end_block: Optional[int] = SAFE_USDE_END_BLOCK,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=summary_cols or [SummaryColumn.SAFE_USDE_ON_SAFE_PTS],
            reward_multiplier=reward_multiplier,
            balance_multiplier=1,
            excluded_addresses=None,
            end_block=end_block,
        )
        self.w3 = W3_BY_CHAIN[chain]["w3"]
        self.usde_contract = self.w3.eth.contract(
            address=USDE_TOKEN_ADDRESS, abi=ERC20_ABI
        )
        self._safe_cache: Dict[ChecksumAddress, bool] = {}
        self._last_scanned_block: Optional[int] = None

    def _load_safes_from_csv(self) -> Set[str]:
        safes: Set[str] = set()
        if not SAFE_ADDRESSES_CSV.exists():
            logging.warning(f"Safe addresses CSV not found: {SAFE_ADDRESSES_CSV}")
            return safes
        with open(SAFE_ADDRESSES_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row.get("address", "").strip()
                if addr:
                    safes.add(Web3.to_checksum_address(addr))
        logging.info(f"Loaded {len(safes)} Safe addresses from CSV")
        return safes

    def _is_contract(self, address: ChecksumAddress) -> bool:
        code = self.w3.eth.get_code(address)
        return len(code) > 0

    def _is_safe(self, address: ChecksumAddress) -> bool:
        import time
        import requests
        if address in self._safe_cache:
            return self._safe_cache[address]
        try:
            url = f"{SAFE_API_URL}/api/v1/safes/{address}/"
            headers = {}
            if SAFE_API_KEY:
                headers["Authorization"] = f"Bearer {SAFE_API_KEY}"
            resp = requests.get(url, headers=headers, timeout=10)
            time.sleep(0.2)  # rate limit: 5 req/sec
            is_safe = resp.status_code == 200
            self._safe_cache[address] = is_safe
            return is_safe
        except Exception as e:
            logging.warning(f"Safe API check failed for {address}: {e}")
            self._safe_cache[address] = False
            return False

    def get_participants(self, blocks: Optional[List[int]] = None) -> Set[str]:
        if not self.participants:
            self.participants = self._load_safes_from_csv()
            for addr in self.participants:
                self._safe_cache[Web3.to_checksum_address(addr)] = True

        self._scan_for_new_safes()
        return self.participants

    def _scan_for_new_safes(self) -> None:
        from_block = self._last_scanned_block + 1 if self._last_scanned_block else self.start_block
        to_block = self.end_block or self.w3.eth.block_number

        if from_block > to_block:
            return

        logging.info(f"Scanning for new Safe participants from block {from_block} to {to_block}...")
        candidate_addresses: Set[ChecksumAddress] = set()

        current = from_block
        while current <= to_block:
            end = min(current + PAGINATION_SIZE - 1, to_block)
            logging.info(f"Fetching Transfer logs from {current} to {end}...")
            transfers = fetch_events_logs_with_retry(
                "USDe Transfer",
                self.usde_contract.events.Transfer(),
                current,
                end,
            )
            for tx in transfers:
                candidate_addresses.add(Web3.to_checksum_address(tx["args"]["from"]))
                candidate_addresses.add(Web3.to_checksum_address(tx["args"]["to"]))
            current = end + 1

        self._last_scanned_block = to_block
        new_addresses = candidate_addresses - self.participants
        logging.info(f"Found {len(new_addresses)} new candidate addresses to check")

        new_safes = 0
        for addr in new_addresses:
            if addr == "0x0000000000000000000000000000000000000000":
                continue
            if addr in self._safe_cache:
                if self._safe_cache[addr]:
                    self.participants.add(addr)
                    new_safes += 1
                continue
            if not self._is_contract(addr):
                self._safe_cache[addr] = False
                continue
            if self._is_safe(addr):
                self.participants.add(addr)
                new_safes += 1

        logging.info(f"Added {new_safes} new Safe addresses (total: {len(self.participants)})")

    def get_block_balances(
        self, cached_data: Dict[int, Dict[ChecksumAddress, float]], blocks: List[int]
    ) -> Dict[int, Dict[ChecksumAddress, float]]:
        logging.info(f"Getting block balances for {len(blocks)} blocks...")
        if not self.participants:
            self.get_participants()

        result: Dict[int, Dict[ChecksumAddress, float]] = {}
        participants_list = list(self.participants)

        for block in blocks:
            if block in cached_data:
                result[block] = cached_data[block]
                continue

            if block < self.start_block:
                result[block] = {}
                continue

            calls = [
                (self.usde_contract, "balanceOf", [addr]) for addr in participants_list
            ]
            balances_raw = multicall_by_address(
                wb3=self.w3,
                multical_address=MULTICALL_ADDRESS_BY_CHAIN.get(
                    self.chain, "0xcA11bde05977b3631167028862bE2a173976CA11"
                ),
                calls=calls,
                block_identifier=block,
                allow_failure=True,
            )

            block_balances: Dict[ChecksumAddress, float] = {}
            for i, addr in enumerate(participants_list):
                raw = balances_raw[i]
                if raw is None:
                    continue
                balance_wei = raw[0] if isinstance(raw, tuple) else raw
                balance = round(balance_wei / (10**USDE_DECIMALS), 4)
                if balance > 0:
                    block_balances[Web3.to_checksum_address(addr)] = balance

            result[block] = block_balances
            logging.info(
                f"Block {block}: {len(block_balances)} Safes with positive USDe balance"
            )

        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    integration = SafeUSDeOnSafeIntegration(
        integration_id=IntegrationID.SAFE_USDE_ON_SAFE,
        start_block=SAFE_USDE_START_BLOCK,
        end_block=SAFE_USDE_START_BLOCK + 1000,
    )
    participants = integration.get_participants()
    print(f"Found {len(participants)} Safe participants (from CSV + new scans)")
    if participants:
        sample = list(participants)[:5]
        print(f"Sample Safes: {sample}")

    test_blocks = [SAFE_USDE_START_BLOCK]
    balances = integration.get_block_balances(cached_data={}, blocks=test_blocks)
    for blk, bals in balances.items():
        print(f"Block {blk}: {len(bals)} addresses with balance")
        sorted_bals = sorted(bals.items(), key=lambda x: x[1], reverse=True)[:5]
        for addr, bal in sorted_bals:
            print(f"  {addr}: {bal:,.4f} USDe")

