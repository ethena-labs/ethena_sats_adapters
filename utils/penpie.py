from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from constants.penpie import PENDLE_LOCKER_ETHEREUM
from constants.penpie import PENDLE_LOCKER_ARBITRUM
from constants.penpie import master_penpie_ethereum
from constants.penpie import master_penpie_arbitrum
from constants.penpie import auto_compound_manager_ethereum
import logging
import json
from utils.web3_utils import (
    fetch_events_logs_with_retry,
    call_with_retry,
    w3,
    w3_arb,
)
from typing import Optional, Set
from web3.contract import Contract
from eth_typing import ChecksumAddress

with open("abi/penpie_master.json") as f:
    master_penpie = json.load(f)
with open("abi/pendle_lpt.json") as f:
    lpt_abi = json.load(f)
with open("abi/ERC20_abi.json") as f:
    erc20_abi = json.load(f)
with open("abi/penpie_tokens.json") as f:
    penpie_tokens = json.load(f)


class PENPIEIntegration(Integration):
    def __init__(
        self,
        integration_id: IntegrationID,
        start_block: int,
        lp_contract: str,
        chain: Chain,
        reward_multiplier: int,
        balance_multiplier: int,
        excluded_addresses: Optional[Set[ChecksumAddress]] = None,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            reward_multiplier=reward_multiplier,
            balance_multiplier=balance_multiplier,
            excluded_addresses=excluded_addresses,
        )
        self.lp_contract = lp_contract

    def get_balance(self, user: str, block: int | str = "latest") -> float:
        if self.chain == Chain.ETHEREUM:
            masterpenpiecontract = w3.eth.contract(
                address=master_penpie_ethereum, abi=master_penpie
            )
        if self.chain == Chain.ARBITRUM:
            masterpenpiecontract = w3_arb.eth.contract(
                address=w3_arb.to_checksum_address(master_penpie_arbitrum),
                abi=master_penpie,
            )

        # Get lpt token address from Stake DAO vault
        pendlePoolAddress = call_with_retry(
            masterpenpiecontract.functions.receiptToStakeToken(self.lp_contract),
            block,
        )
        # pendlePoolAddress = "0x107a2e3cD2BB9a32B9eE2E4d51143149F8367eBa"
        if self.chain == Chain.ETHEREUM:
            lptContract = w3.eth.contract(address=pendlePoolAddress, abi=lpt_abi)
        if self.chain == Chain.ARBITRUM:
            lptContract = w3_arb.eth.contract(address=pendlePoolAddress, abi=lpt_abi)
        print(pendlePoolAddress)
        # Get SY address
        tokens = call_with_retry(
            lptContract.functions.readTokens(),
            block,
        )

        sy = tokens[0]
        if self.chain == Chain.ETHEREUM:
            sy_contract = w3.eth.contract(address=sy, abi=erc20_abi)
        if self.chain == Chain.ARBITRUM:
            sy_contract = w3_arb.eth.contract(address=sy, abi=erc20_abi)

        # Get SY balance in the Pendle pool
        sy_bal = call_with_retry(
            sy_contract.functions.balanceOf(pendlePoolAddress),
            block,
        )
        if sy_bal == 0:
            return 0
        if self.chain == Chain.ETHEREUM:
            PENDLE_LOCKER = PENDLE_LOCKER_ETHEREUM
        if self.chain == Chain.ARBITRUM:
            PENDLE_LOCKER = PENDLE_LOCKER_ARBITRUM
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
        print(sy_bal / 10**18)
        print(lpt_bal / 10**18)

        if self.chain == Chain.ETHEREUM:
            receiptcontract = w3.eth.contract(
                address=w3.to_checksum_address(self.lp_contract), abi=erc20_abi
            )
        if self.chain == Chain.ARBITRUM:
            receiptcontract = w3_arb.eth.contract(
                address=w3_arb.to_checksum_address(self.lp_contract), abi=erc20_abi
            )

        # Get gauge total suply
        penpeiepoolTotalSupply = call_with_retry(
            receiptcontract.functions.totalSupply(),
            block,
        )

        # Get gauge user balance
        userpenpeiepoolBal = call_with_retry(
            receiptcontract.functions.balanceOf(user),
            block,
        )

        # Get user share based on gauge#totalSupply / gauge#balanceOf(user) and lockerSyBalance
        userShare = userpenpeiepoolBal * 100 / penpeiepoolTotalSupply

        print(user, userShare * lpt_bal / 100)
        return userShare * lockerSyBalance / 100

    def get_participants(self, blocks: list[int] | None) -> set[str]:
        if self.participants is not None:
            return self.participants

        self.participants = self.get_penpie_participants()
        logging.info(
            f"[{self.get_description()}] Found {len(self.participants)} participants"
        )
        return self.participants

    def get_penpie_participants(self):
        all_users = set()
        start = self.start_block

        if self.chain == Chain.ETHEREUM:
            contract = w3.eth.contract(
                address=w3.to_checksum_address(self.lp_contract), abi=erc20_abi
            )
        elif self.chain == Chain.ARBITRUM:
            contract = w3_arb.eth.contract(
                address=w3_arb.to_checksum_address(self.lp_contract), abi=erc20_abi
            )
        else:
            return set()
        page_size = 1900
        if self.chain == Chain.ETHEREUM:
            target_block = w3.eth.get_block_number()
        elif self.chain == Chain.ARBITRUM:
            target_block = w3_arb.eth.get_block_number()
        else:
            return set()
        while start < target_block:
            to_block = min(start + page_size, target_block)
            deposits = fetch_events_logs_with_retry(
                f"Penpie users {self.lp_contract}",
                contract.events.Transfer(),
                start,
                to_block,
            )
            # print(start, to_block, len(deposits), "getting Stake DAO contract data")
            for deposit in deposits:
                if (
                    deposit["args"]["to"]
                    != "0x0000000000000000000000000000000000000000"
                ):
                    all_users.add(deposit["args"]["to"])
                    print(deposit["args"]["to"])
            start += page_size

        return all_users
