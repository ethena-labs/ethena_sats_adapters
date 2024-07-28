from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.equilibria import PENDLE_LOCKER_ETHEREUM
from constants.equilibria import equilibria_deposit_ethereum
import json
from utils.web3_utils import (
    fetch_events_logs_with_retry,
    call_with_retry,
    w3,
    w3_arb,
)
from typing import List

with open("abi/equilibria_deposit.json") as f:
    equilibria_deposit = json.load(f)
with open("abi/pendle_lpt.json") as f:
    lpt_abi = json.load(f)
with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)
with open("abi/equilibria_lpt.json") as f:
    equilibria_lpt = json.load(f)


class EquilibriaIntegration(Integration):
    def __init__(
            self,
            integration_id: IntegrationID,
            start_block: int,
            lp_contract: str,
            lp_contract_id: int,
            chain: Chain,
            reward_multiplier: int,
            balance_multiplier: int,
            excluded_addresses: List[str],
    ):
        super().__init__(
            integration_id,
            start_block,
            chain,
            None,
            reward_multiplier,
            balance_multiplier,
            excluded_addresses,
            None,
            None,
        )
        self.lp_contract = lp_contract
        self.lp_contract_id = lp_contract_id

    def get_balance(self, user: str, block: int) -> float:
        equilibria_deposit_contract = w3.eth.contract(address=equilibria_deposit_ethereum, abi=equilibria_deposit)

        # Get lpt token address from Stake DAO vault
        poolInfo = call_with_retry(
            equilibria_deposit_contract.functions.poolInfo(self.lp_contract_id),
            block,
        )
        pendle_market_address = poolInfo[0]
        # print("lp contract", self.lp_contract)
        # print('self lp contract id', self.lp_contract_id)
        # print("pendlePoolAddress", poolInfo[0])

        # pendlePoolAddress = "0x107a2e3cD2BB9a32B9eE2E4d51143149F8367eBa"
        lptContract = w3.eth.contract(address=pendle_market_address, abi=lpt_abi)
        # Get SY address
        tokens = call_with_retry(
            lptContract.functions.readTokens(),
            block,
        )
        # print("tokens", tokens)
        sy = tokens[0]
        sy_contract = w3.eth.contract(address=sy, abi=erc20_abi)

        # Get SY balance in the Pendle pool
        sy_bal = call_with_retry(
            sy_contract.functions.balanceOf(pendle_market_address),
            block,
        )
        print("sy_bal", sy_bal)
        if sy_bal == 0:
            return 0
        PENDLE_LOCKER = PENDLE_LOCKER_ETHEREUM
        # Get Equilibria lpt balance
        lpt_bal = call_with_retry(
            lptContract.functions.activeBalance(PENDLE_LOCKER),
            block,
        )
        print("lpt_bal", lpt_bal)
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

        lockerSyBalance = round(((sy_bal / 10 ** 18) * lpt_bal) / total_active_supply, 4)
        print(sy_bal / 10 ** 18)
        print(lpt_bal / 10 ** 18)

        receipt_contract = w3.eth.contract(address=self.lp_contract, abi=erc20_abi)

        # Get gauge total suply
        equilibria_pool_TotalSupply = call_with_retry(
            receipt_contract.functions.totalSupply(),
            block,
        )

        print('equilibria_pool_TotalSupply', equilibria_pool_TotalSupply)
        # Get gauge user balance
        user_equilibria_pool_bal = call_with_retry(
            receipt_contract.functions.balanceOf(user),
            block,
        )
        print('user_equilibria_pool_bal', user_equilibria_pool_bal)

        # Get user share based on gauge#totalSupply / gauge#balanceOf(user) and lockerSyBalance
        userShare = user_equilibria_pool_bal * 100 / equilibria_pool_TotalSupply

        # print(user, userShare * lpt_bal / 100)
        print('userShare  lockerSyBalance:', userShare * lockerSyBalance / 100)
        print('-------------------------------------------------')
        return userShare * lockerSyBalance / 100

    def get_participants(self) -> list:
        if self.participants is not None:
            return self.participants

        self.participants = self.get_equilibria_participants()
        return self.participants

    def get_equilibria_participants(self):
        all_users = set()

        start = self.start_block
        contract = w3.eth.contract(address=self.lp_contract, abi=equilibria_lpt)
        page_size = 1900
        target_block = w3.eth.get_block_number()
        while start < target_block:
            to_block = min(start + page_size, target_block)
            deposits = fetch_events_logs_with_retry(
                f"Equilibria users {self.lp_contract}",
                contract.events.Staked(),
                start,
                to_block,
            )
            print('deposits', deposits)
            print(start, to_block, len(deposits), "getting Equilibria Finance contract data")
            for deposit in deposits:
                if (deposit["args"]["_user"]):
                    all_users.add(deposit["args"]["_user"])
                    print(deposit["args"]["_user"])
            start += page_size
        print('all_users', len(all_users))
        print('-------------------------------------------------')
        return all_users
