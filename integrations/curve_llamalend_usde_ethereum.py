from constants.chains import Chain
from constants.integration_ids import IntegrationID
from constants.summary_columns import SummaryColumn

import constants.curve as curve_constants
import utils.curve as curve_utils

from models.integration import Integration
from utils.web3_utils import fetch_events_logs_with_retry, w3_arb, call_with_retry


class CurveLlamaLendUSDeEthereum(Integration):
    def __init__(self):
        super().__init__(
            integration_id=IntegrationID.CURVE_USDE_BORROWERS,
            start_block=curve_constants.CURVE_LLAMALEND_ETHEREUM_USDE_GENESIS_BLOCK,
            chain=Chain.ETHEREUM,
            summary_cols=[SummaryColumn.CURVE_LLAMALEND_SHARDS],
            reward_multiplier=5,
            balance_multiplier=1,
        )

    def get_balance(self, user: str, block: int) -> float:
        
        # get the account NFT balance
        user_state = call_with_retry(
            curve_utils.curve_llamalend_usde_controller_contract.functions.user_state(user),
            block,
        )
        # user_state returns [collateral, borrowable, debt, nbands] and we need collateral
        return user_state[0] / 1e18

    def get_participants(self) -> list:
        page_size = 1900
        start_block = curve_constants.CURVE_LLAMALEND_ETHEREUM_USDE_GENESIS_BLOCK
        target_block = w3_arb.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            borrows = fetch_events_logs_with_retry(
                f"Synthetix V3 Arbitrum users from {start_block} to {to_block}",
                curve_utils.curve_llamalend_usde_controller_contract.events.Borrow(),
                start_block,
                to_block,
            )
            for borrow_instance in borrows:
                all_users.add(borrow_instance["args"]["user"])
            start_block += page_size

        all_users = list(all_users)
        self.participants = all_users
        return all_users


if __name__ == "__main__":
    curve_llamalend_usde_crvusd = CurveLlamaLendUSDeEthereum()
    print(curve_llamalend_usde_crvusd.get_participants())
    print(curve_llamalend_usde_crvusd.get_balance(curve_llamalend_usde_crvusd.participants[0], 227610000))