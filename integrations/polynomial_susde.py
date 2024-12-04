from constants.chains import Chain
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import w3_polynomial, fetch_events_logs_with_retry, call_with_retry
from utils.polynomial import core_proxy_contract, core_account_proxy_contract
from constants.polynomial import POLYNOMIAL_DEPLOYMENT_BLOCK, POLYNOMIAL_USDE_TOKEN_ADDRESS


class PolynomialIntegration(Integration): 
      def __init__(self):
        super().__init__(
            IntegrationID.POLYNOMIAL_SUSDE,
            POLYNOMIAL_DEPLOYMENT_BLOCK,
            Chain.POLYNOMIAL,
            [],
            5,
            1,
            None,
            None,
        )
        self.blocknumber_to_susdeVaults = {}

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
                    account_id, POLYNOMIAL_USDE_TOKEN_ADDRESS
                ),
                block,
            )
            total_balance += balance
        return total_balance / 1e18

      def get_participants(self, blocks: list[int] | None) -> set[str]:
        page_size = 1900
        start_block = 60000000
        target_block = w3_polynomial.eth.get_block_number()

        all_users: set[str] = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"Polynomial users from {start_block} to {to_block}",
                core_account_proxy_contract.events.Transfer(),
                start_block,
                to_block,
            )
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
            
            start_block += page_size

        self.participants = all_users
        print(all_users)
        return all_users


if __name__ == "__main__":
    polynomial = PolynomialIntegration()
    participants = polynomial.get_participants(None)
    print(len(participants))
    print(polynomial.get_balance(list(participants)[0], 7557919))
