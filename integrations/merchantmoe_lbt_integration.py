import logging

from web3.contract import Contract

from constants.chains import Chain
from constants.integration_ids import IntegrationID
from constants.merchantmoe import (
    ZERO_ADDRESS,
    DEAD_ADDRESS,
    METH_USDE_MERCHANT_MOE_LBT_DEPLOYMENT_BLOCK,
    METH_USDE_MERCHANT_MOE_LBT_CONTRACT,
)
from models.integration import Integration
from utils.merchantmoe import lb_pair_contract, liquidity_helper_contract
from utils.web3_utils import W3_BY_CHAIN, fetch_events_logs_with_retry, call_with_retry


class MerchantMoeIntegration(Integration):
    def __init__(
        self,
        start_block: int,
        lbt_contract: Contract,
        liquidity_helper_contract: Contract
    ):
        super().__init__(
            IntegrationID.MERCHANT_MOE_METH_USDE_LBT,
            start_block,
            Chain.MANTLE,
            None,
            20,
            1,
            None,
            None,
        )
        self.name = "MerchantMoe"
        self.lbt_contract = lbt_contract
        self.liquidity_helper_contract = liquidity_helper_contract


    def get_balance(self, user: str, block: int) -> float:
        active_id = call_with_retry(
            self.lbt_contract.functions.getActiveId(),
            block
        )

        # calculate the amount in bins for ids that are +/- 20% from active price
        # 10bp pair, log(1.20)/log(1.001) = 183 bins each side of range
        lower_bin_bound = active_id - 183
        upper_bin_bound = active_id + 183
        bin_range = list(range(lower_bin_bound, upper_bin_bound + 1))

        total_liquidity = 0
        logging.info(f"[{self.name}] Calling Liquidity Helper Contract for User: {user}, for bin ids: {bin_range}")
        liquidity = call_with_retry(
            self.liquidity_helper_contract.functions.getLiquiditiesOf(
                METH_USDE_MERCHANT_MOE_LBT_CONTRACT, user, bin_range
            ),
            block
        )
        total_liquidity += sum(liquidity)

        total_liquidity = round(total_liquidity / 10**18, 8)

        logging.info(f"[{self.name}] {user} has {total_liquidity} total liquidity within 20% range of the active price")
        return total_liquidity

    def get_participants(self) -> list:
        if self.participants is not None:
            return self.participants

        logging.info(f"[{self.name}] Getting participants...")
        page_size = 1900
        start_block = self.start_block
        w3_client = W3_BY_CHAIN["mantle"]["w3"]
        target_block = w3_client.eth.get_block_number()
        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"{self.name} LBT TransferBatch events",
                self.lbt_contract.events.TransferBatch(),
                start_block,
                to_block
            )

            logging.info(f"[{self.name}] Scanning blocks {start_block} to {to_block}, received {len(transfers)} mETH/USDe transfer events")
            for transfer in transfers:
                from_address = transfer["args"]["from"]
                to_address = transfer["args"]["to"]

                if from_address != ZERO_ADDRESS and from_address != DEAD_ADDRESS:
                    all_users.add(from_address)
                if to_address != ZERO_ADDRESS and to_address != DEAD_ADDRESS:
                    all_users.add(to_address)

            start_block += page_size

        logging.info(f"[{self.name}] {len(all_users)} users found")
        self.participants = all_users
        return list(all_users)


if __name__ == "__main__":
    merchant_moe_integration = MerchantMoeIntegration(
        METH_USDE_MERCHANT_MOE_LBT_DEPLOYMENT_BLOCK,
        lb_pair_contract,
        liquidity_helper_contract,
    )
    print(merchant_moe_integration.get_participants())
    print(merchant_moe_integration.get_balance(list(merchant_moe_integration.get_participants())[1], "latest"))
