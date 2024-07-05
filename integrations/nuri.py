from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from constants.nuri import NURI_NFP_MANAGER_ADDRESS, NURI_POOL_ADDRESS, NURI_DEPLOYMENT_BLOCK
from constants.summary_columns import SummaryColumn
from utils.nuri import nfp_manager, pool
from utils.web3_utils import w3_scroll, fetch_events_logs_with_retry, call_with_retry
from web3 import Web3

class Nuri(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.NURI_USDE_LP,
            NURI_DEPLOYMENT_BLOCK,
            Chain.SCROLL,
            [SummaryColumn.NURI_SHARDS],
            20,
            1,
        )

    def get_balance(self, user: str, block: int) -> float:      
        balance = call_with_retry(
            nfp_manager.functions.balanceOf(user),
            block,
        )

        print(balance)

        positions = []

        for i in range(balance):
            tokenOfOwnerByIndex = call_with_retry(
                nfp_manager.functions.tokenOfOwnerByIndex(user, i),
                block,
            )

            positions.append(tokenOfOwnerByIndex)

        print(positions)

        for position in positions:
            position_info = call_with_retry(
                nfp_manager.functions.positions(position),
                block,
            )
            print(position_info)

        # get pool current tick
        current_tick = call_with_retry(
            pool.functions.slot0(),
            block,
        )

        
        return position_info[0]

    def get_participants(self) -> list:
        page_size = 999
        start_block = NURI_DEPLOYMENT_BLOCK
        target_block = w3_scroll.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"Nuri users from {start_block} to {to_block}",
                nfp_manager.events.Transfer(),
                start_block,
                to_block,
            )
            print(transfers)
            

            total_supply = call_with_retry(
                nfp_manager.functions.totalSupply(),
                target_block,
            )
            print(total_supply)
            for i in range(total_supply):
                try:
                    deposits = call_with_retry(
                        nfp_manager.functions.ownerOf(i),
                        start_block,
                    )
                except:
                    continue

                all_users.update(deposits)

            start_block += page_size


        all_users = list(all_users)
        self.participants = all_users
        return all_users
    
if __name__ == "__main__":
    nuri = Nuri()
    #print(nuri.get_balance(Web3.to_checksum_address("0xCAfc58De1E6A071790eFbB6B83b35397023E1544"), 7081747))
    print(nuri.get_participants())
    print(nuri.get_balance(nuri.participants[0], 7055711))
