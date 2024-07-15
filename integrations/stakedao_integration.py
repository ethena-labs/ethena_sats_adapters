import logging
from typing import List
from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from utils.web3_utils import (
    fetch_events_logs_with_retry,
    call_with_retry,
)
from utils.web3_utils import w3

vault_abi = load_abi("stakedao_vault.json")
lpt_abi = load_abi("pendle_lpt.json")
erc20_abi = load_abi("ERC20_abi.json")


class StakeDAOIntegration(Integration):
    # pylint: disable=dangerous-default-value
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        lp_contract: str,
        chain: Chain = Chain.ETHEREUM,
        summary_cols: list[SummaryColumn] = None,
        reward_multiplier: int = 20,
        balance_multiplier: int = 1,
        excluded_addresses: List[str] = [STAKEDAO_PENDLE_LOCKER],
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            summary_cols,
            reward_multiplier,
            balance_multiplier,
            excluded_addresses,
            None,
            None,
        )
        self.lp_contract = lp_contract
        self.summary_cols = (
            [SummaryColumn.PENDLE_SHARDS] if summary_cols is None else summary_cols
        )

    def get_balance(self, user: str, block: int) -> float:
        stakedao_vault_contract = w3.eth.contract(
            address=self.lp_contract, abi=vault_abi
        )
        # Get lpt token address from Stake DAO vault
        pendle_pool_address = call_with_retry(
            stakedao_vault_contract.functions.token(),
            block,
        )
        lpt_contract = w3.eth.contract(address=pendle_pool_address, abi=lpt_abi)
        # Get SY address
        tokens = call_with_retry(
            lpt_contract.functions.readTokens(),
            block,
        )
        sy = tokens[0]
        sy_contract = w3.eth.contract(address=sy, abi=erc20_abi)
        # Get SY balance in the Pendle pool
        sy_bal = call_with_retry(
            sy_contract.functions.balanceOf(pendle_pool_address),
            block,
        )
        if sy_bal == 0:
            return 0
        # Get Stake DAO lpt balance
        lpt_bal = call_with_retry(
            lpt_contract.functions.activeBalance(STAKEDAO_PENDLE_LOCKER),
            block,
        )
        if lpt_bal == 0:
            return 0
        # Get LPT total supply
        total_active_supply = call_with_retry(
            lpt_contract.functions.totalActiveSupply(),
            block,
        )
        if total_active_supply == 0:
            print("total_active_supply is 0")
            return 0
        locker_sy_bal = round(((sy_bal / 10**18) * lpt_bal) / total_active_supply, 4)
        # Get stake dao liquidity gauge
        sd_guage_address = call_with_retry(
            stakedao_vault_contract.functions.liquidityGauge(),
            block,
        )
        sd_gauge_contract = w3.eth.contract(address=sd_guage_address, abi=erc20_abi)
        # Get gauge total suply
        sd_guage_total_supply = call_with_retry(
            sd_gauge_contract.functions.totalSupply(),
            block,
        )
        # Get gauge user balance
        user_sd_guage_bal = call_with_retry(
            sd_gauge_contract.functions.balanceOf(user),
            block,
        )
        # Get user share based on gauge#totalSupply / gauge#balanceOf(user) and lockerSyBalance
        user_share = user_sd_guage_bal * 100 / sd_guage_total_supply
        print(user, user_share * locker_sy_bal / 100)
        return user_share * locker_sy_bal / 100

    def get_participants(self, _: List[int] = None) -> list:
        logging.info(f"[{self.get_description()}] Getting participants...")
        participants = set()
        start = self.get_new_blocks_start()
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
                participants.add(deposit["args"]["_depositor"])
            start += page_size
        logging.info(
            f"[{self.get_description()}] Found {len(participants)} participants"
        )
        return list(participants)
