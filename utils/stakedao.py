from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from constants.stakedao import PENDLE_LOCKER
import logging
import json
from utils.web3_utils import (
    fetch_events_logs_with_retry,
    call_with_retry,
    w3,
)
from typing import List

with open("abi/stakedao_vault.json") as f:
    vault_abi = json.load(f)
with open("abi/pendle_lpt.json") as f:
    lpt_abi = json.load(f)
with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)


class StakeDAOIntegration(Integration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        lp_contract: str,
        chain: Chain = Chain.ETHEREUM,
        reward_multiplier: int = 20,
        balance_multiplier: int = 1,
        excluded_addresses: List[str] = [PENDLE_LOCKER],
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            None,
            reward_multiplier,
            balance_multiplier=balance_multiplier,
            excluded_addresses=excluded_addresses,
        )
        self.lp_contract = lp_contract

    def get_balance(self, user: str, block: int) -> float:

        stakeDAOVaultContract = w3.eth.contract(
            address=w3.to_checksum_address(self.lp_contract), abi=vault_abi
        )

        # Get lpt token address from Stake DAO vault
        pendlePoolAddress = call_with_retry(
            stakeDAOVaultContract.functions.token(),
            block,
        )

        lptContract = w3.eth.contract(address=pendlePoolAddress, abi=lpt_abi)

        # Get SY address
        tokens = call_with_retry(
            lptContract.functions.readTokens(),
            block,
        )

        sy = tokens[0]
        sy_contract = w3.eth.contract(address=sy, abi=erc20_abi)

        # Get SY balance in the Pendle pool
        sy_bal = call_with_retry(
            sy_contract.functions.balanceOf(pendlePoolAddress),
            block,
        )
        if sy_bal == 0:
            return 0

        # Get Stake DAO lpt balance
        lpt_bal = call_with_retry(
            lptContract.functions.activeBalance(PENDLE_LOCKER),
            block,
        )
        if lpt_bal == 0:
            return 0

        # Get LPT total supply
        total_active_supply = call_with_retry(
            lptContract.functions.totalActiveSupply(),
            block,
        )
        if total_active_supply == 0:
            print("total_active_supply is 0")
            return 0

        lockerSyBalance = round(((sy_bal / 10**18) * lpt_bal) / total_active_supply, 4)

        # Get stake dao liquidity gauge
        sdGaugeAddress = call_with_retry(
            stakeDAOVaultContract.functions.liquidityGauge(),
            block,
        )

        sd_gauge_contract = w3.eth.contract(address=sdGaugeAddress, abi=erc20_abi)

        # Get gauge total suply
        sdGaugeTotalSupply = call_with_retry(
            sd_gauge_contract.functions.totalSupply(),
            block,
        )

        # Get gauge user balance
        userSdGaugeBal = call_with_retry(
            sd_gauge_contract.functions.balanceOf(user),
            block,
        )

        # Get user share based on gauge#totalSupply / gauge#balanceOf(user) and lockerSyBalance
        userShare = userSdGaugeBal * 100 / sdGaugeTotalSupply

        print(user, userShare * lockerSyBalance / 100)
        return userShare * lockerSyBalance / 100

    def get_participants(self) -> list:
        if self.participants is not None:
            return self.participants

        logging.info(f"[{self.get_description()}] Getting participants...")
        self.participants = self.get_stakedao_participants()
        logging.info(
            f"[{self.get_description()}] Found {len(self.participants)} participants"
        )
        return self.participants

    def get_stakedao_participants(self):
        all_users = set()

        start = self.start_block
        contract = w3.eth.contract(address=self.lp_contract, abi=vault_abi)
        page_size = 1900
        target_block = w3.eth.get_block_number()
        while start < target_block:
            to_block = min(start + page_size, target_block)
            deposits = fetch_events_logs_with_retry(
                f"Stake DAO users {self.lp_contract}",
                contract.events.Deposit(),
                start,
                to_block,
            )
            print(start, to_block, len(deposits), "getting Stake DAO contract data")
            for deposit in deposits:
                all_users.add(deposit["args"]["_depositor"])
            start += page_size

        return all_users
