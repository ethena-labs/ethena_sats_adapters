from constants.chains import Chain
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import w3_polynomial, fetch_events_logs_with_retry, call_with_retry
from utils.polynomial import core_proxy_contract, core_account_proxy_contract
from constants.polynomial import POLYNOMIAL_DEPLOYMENT_BLOCK, POLYNOMIAL_USDE_TOKEN_ADDRESS
import requests


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
        # First get the SCW addresses for this EOA
        api_url = f"https://perps-api-mainnet.polynomial.finance/core/zerodev-accounts?eoa={user}&chainId=80088"
        total_balance = 0
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                response = response.json()
                if len(response) > 0 and "address" in response[0]:
                    scw_address = response[0]["address"]
                    # Get the account NFT balance for this SCW
                    balance = call_with_retry(
                        core_account_proxy_contract.functions.balanceOf(scw_address),
                        block,
                    )
                    # Loop through the balance and get the account ids
                    for i in range(balance):
                        account_id = call_with_retry(
                            core_account_proxy_contract.functions.tokenOfOwnerByIndex(scw_address, i),
                            block,
                        )
                        # Get collateral balance for this account id
                        _, balance, _ = call_with_retry(
                            core_proxy_contract.functions.getAccountCollateral(
                                account_id, POLYNOMIAL_USDE_TOKEN_ADDRESS
                            ),
                            block,
                        )
                        total_balance += balance
                        
        except Exception as e:
            print(f"Error fetching data for EOA {user}: {e}")
        
        return total_balance / 1e18

      def get_participants(self, blocks: list[int] | None) -> set[str]:
        page_size = 1900
        start_block = POLYNOMIAL_DEPLOYMENT_BLOCK
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
                address = transfer["args"]["to"]
                # Query the Polynomial API for each address
                api_url = f"https://perps-api-mainnet.polynomial.finance/core/zerodev-accounts/owner?zerodevAccount={address}&chainId=8008"
                try:
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        owner = response.text.strip().strip('"')  # Remove quotes from response
                        all_users.add(owner)
                except Exception as e:
                    print(f"Error fetching data for address {address}: {e}")
            
            start_block += page_size

        self.participants = all_users
        return all_users


if __name__ == "__main__":
    polynomial = PolynomialIntegration()
    participants = polynomial.get_participants(None)
    print(len(participants))
    print(polynomial.get_balance(list(participants)[0], 8978929))
