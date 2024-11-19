from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from models.integration import Integration
from constants.synthetix import SYNTHETIX_ARB_DEPLOYMENT_BLOCK, ARB_USDE_TOKEN_ADDRESS
from constants.summary_columns import SummaryColumn
from utils.synthetix import core_proxy_contract, core_account_proxy_contract
from utils.web3_utils import w3_arb, fetch_events_logs_with_retry, call_with_retry


class Synthetix(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.SYNTHETIX_USDE_LP,
            SYNTHETIX_ARB_DEPLOYMENT_BLOCK,
            Chain.ARBITRUM,
            [SummaryColumn.SYNTHETIX_ARBITRUM_SHARDS],
            20,
            1,
        )

    def get_balance(self, user: str, block: int) -> float:
        # get the account NFT balance
        balance = call_with_retry(
            core_account_proxy_contract.functions.balanceOf(user),
            block,
        )

        # loop through the balance and get the account ids
        account_ids = []
        for i in range(balance):
            account_id = call_with_retry(
                core_account_proxy_contract.functions.tokenOfOwnerByIndex(user, i),
                block,
            )
            account_ids.append(account_id)

        # for each account id, check the balance
        total_balance = 0
        for account_id in account_ids:
            _, balance, _ = call_with_retry(
                core_proxy_contract.functions.getAccountCollateral(
                    account_id, ARB_USDE_TOKEN_ADDRESS
                ),
                block,
            )
            total_balance += balance
        return total_balance / 1e18

    def get_participants(self) -> list:
        page_size = 1900
        start_block = SYNTHETIX_ARB_DEPLOYMENT_BLOCK
        target_block = w3_arb.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"Synthetix V3 Arbitrum users from {start_block} to {to_block}",
                core_account_proxy_contract.events.Transfer(),
                start_block,
                to_block,
            )
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
            start_block += page_size

        all_users = list(all_users)
        self.participants = all_users
        return all_users


if __name__ == "__main__":
    synthetix = Synthetix()
    print(synthetix.get_participants())
    print(synthetix.get_balance(synthetix.participants[0], 227610000))
