from typing import List
import requests
from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from constants.integration_token import Token
from constants.summary_columns import SummaryColumn
from models.integration import Integration


###############################################################################
# Integration helpers #########################################################
###############################################################################

term_finance_subgraph_url_mainnet = "https://public-graph-proxy.mainnet.termfinance.io"

borrower_balance_query = """{{
    termRepoCollaterals(
        where: {{
            collateralToken: "{collateralToken}", 
            repoExposure_: {{
                borrower: "{borrower}"
            }}
        }},
        block: {{
            number: {block}
        }}
    ) {{
        repoExposure {{
            borrower
        }}
        amountLocked
    }}
    termBidCollaterals(
        where: {{
            collateralToken: "{collateralToken}", 
            bid_: {{
                bidder: "{borrower}",
                assignedAmount: 0,
                locked: true
            }}
        }},
        block: {{
            number: {block}
        }}
    ) {{
        bid {{
            bidder
        }}
        collateralToken
        amount
    }}
}}
"""

participants_query = """{{
    termRepoCollaterals(
        where: {{
            collateralToken: "{collateralToken}",
            amountLocked_gt: 0,
        }},
    ) {{
        repoExposure {{
            borrower
        }}
        amountLocked
    }}
    termBidCollaterals(
        where: {{
            collateralToken: "{collateralToken}", 
            bid_: {{
                assignedAmount: 0,
                locked: true
            }}
        }},
    ) {{
        bid {{
            bidder
        }}
        collateralToken
        amount
    }}
}}
"""

repo_lockers_query = """{
    termRepos(first: 5000) {
        termRepoLocker
    }
}
"""

collateral_token_addresses = {
    Token.SUSDE: "0x9d39a5de30e57443bff2a8307a4256c8797a3497",  # Mainnet address for SUSDE
    # Token.USDE: "0x7e7e112A68d8D2E221E11047f6E4D7a8eB2dC5e1",  # Unsupported
    # Token.ENA: "0x5e0489aF6e9fd2177eA34aa7A3fD5cD205e3fEe6",   # Unsupported
}


# Helper for making graphql queries
def fetch_data(url, query):
    response = requests.post(url, json={"query": query})
    if response.status_code == 200:
        response_json = response.json()
        if "data" not in response_json:
            print(f"Query failed with response: {response_json}")
            return None
        return response_json["data"]
    else:
        print(f"Query failed with status code {response.status_code}")
        return None


###############################################################################
# TermFinance integration #####################################################
###############################################################################


class TermFinanceIntegration(Integration):
    def __init__(self):
        repo_lockers_response = fetch_data(
            url=term_finance_subgraph_url_mainnet,
            query=repo_lockers_query,
        )
        repo_lockers = []
        if repo_lockers_response is not None:
            for result in repo_lockers_response["termRepos"]:
                repo_lockers.append(result["termRepoLocker"])
        super().__init__(
            integration_id=IntegrationID.TERM_SUSDE,
            start_block=16380765,
            chain=Chain.ETHEREUM,
            summary_cols=None,
            reward_multiplier=20,  # TODO: Change 20 to the sats multiplier for the protocol that has been agreed upon
            balance_multiplier=1,  # TODO: Almost always 1, optionally change to a different value if an adjustment needs to be applied to balances
            excluded_addresses=repo_lockers,
            end_block=None,  # No end block, protocol is still active
            reward_multiplier_func=None,  # reward_multiplier should be the same across blocks
        )

    def get_balance(self, user: str, block: int) -> float:
        # Make two queries: one to get borrower repo collateral and one to get borrower bid collateral
        balance_results = fetch_data(
            url=term_finance_subgraph_url_mainnet,
            query=borrower_balance_query.format(
                collateralToken=collateral_token_addresses[self.get_token()],
                borrower=user,
                block=block,
            ),
        )

        # Add the results together (amount + amountLocked) to get the total balance
        total_balance = 0
        if balance_results is not None:
            for result in balance_results["termRepoCollaterals"]:
                total_balance += int(result["amountLocked"])
            for result in balance_results["termBidCollaterals"]:
                total_balance += int(result["amount"])
        else:
            print(f"Failed to get balance for user {user} at block {block}")

        return total_balance

    def get_participants(self) -> list:
        # Make two queries: one to get borrower repo collateral and one to get borrower bid collateral
        participants_results = fetch_data(
            url=term_finance_subgraph_url_mainnet,
            query=participants_query.format(
                collateralToken=collateral_token_addresses[self.get_token()],
            ),
        )

        # Build a set of all possible borrowers (de-duplicating them during set add)
        participants = set()
        if participants_results is not None:
            for result in participants_results["termRepoCollaterals"]:
                participants.add(result["repoExposure"]["borrower"])
            for result in participants_results["termBidCollaterals"]:
                participants.add(result["bid"]["bidder"])
        else:
            print(f"Failed to get participants")

        return list(participants)

    def get_id(self) -> IntegrationID:
        return self.integration_id

    def get_token(self) -> Token:
        return self.integration_id.get_token()

    def get_description(self) -> str:
        return self.integration_id.get_description()

    def get_col_name(self) -> str:
        return self.integration_id.get_column_name()

    def get_chain(self) -> Chain:
        return self.chain

    def get_summary_cols(self) -> list[SummaryColumn]:
        return self.summary_cols

    def get_reward_multiplier(self, block: int) -> int:
        if self.reward_multiplier_func is not None:
            return self.reward_multiplier_func(block)
        return self.reward_multiplier

    def get_balance_multiplier(self) -> int:
        return self.balance_multiplier

    def get_start_block(self) -> int:
        return self.start_block

    def get_end_block(self) -> int:
        if self.end_block is None:
            return (
                2**31 - 1
            )  # if no end block is specified, return the maximum possible block number
        return self.end_block

    def get_excluded_addresses(self) -> List[str]:
        return self.excluded_addresses

    def is_user_a_participant(self, user: str) -> bool:
        if self.participants is None:
            self.get_participants()
        return user in self.participants


###############################################################################
# Tests #######################################################################
###############################################################################

if __name__ == "__main__":
    example_integration = TermFinanceIntegration()
    print(example_integration.get_participants())
    print(
        example_integration.get_balance(
            list(example_integration.get_participants())[0], 20169604
        )
    )
