from constants.chains import Chain
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import w3_polynomial, fetch_events_logs_with_retry, call_with_retry
from utils.polynomial import core_proxy_contract, core_account_proxy_contract, owner_register_contract
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

      def get_balance(self, user: str, block: int) -> float:
        # Fetch all owner registered events
        owner_registered_events = fetch_events_logs_with_retry(
            f"Polynomial OwnerRegistered events for {user}",
            owner_register_contract.events.OwnerRegistered(),
            POLYNOMIAL_DEPLOYMENT_BLOCK,
            block,
        )

        # Filter events in memory
        owner_registered_events = [
            event for event in owner_registered_events 
            if event["args"]["owner"].lower() == user.lower()
        ]

        total_balance = 0
        if owner_registered_events:
            scw_address = owner_registered_events[0]["args"]["kernel"]
            try:
                # Add error handling around the token lookup
                account_id = call_with_retry(
                    core_account_proxy_contract.functions.tokenOfOwnerByIndex(scw_address, 0),
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
                # Silently continue if the user has no tokens
                pass
                    
        return total_balance / 1e18

      def get_participants(self, blocks: list[int] | None) -> set[str]:
        page_size = 100000
        start_block = POLYNOMIAL_DEPLOYMENT_BLOCK
        target_block = w3_polynomial.eth.get_block_number()
        all_users: set[str] = set()

        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)

            # Fetch all owner registered events
            owner_registered_events = fetch_events_logs_with_retry(
                f"Polynomial OwnerRegistered events from {start_block} to {to_block}",
                owner_register_contract.events.OwnerRegistered(),
                start_block,
                to_block
            )

            # filter the eoa addresses
            for event in owner_registered_events:
                owner = event["args"]["owner"].lower()
                all_users.add(owner)

            start_block += page_size

        self.participants = all_users
        return all_users


if __name__ == "__main__":
    polynomial = PolynomialIntegration()
    participants = polynomial.get_participants(None)
    print(len(participants))
    print(polynomial.get_balance(list(participants)[0], 9338341))
