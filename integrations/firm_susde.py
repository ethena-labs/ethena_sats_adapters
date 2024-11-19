from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from models.integration import Integration
from constants.firm import FIRM_SUSDE_DEPLOYMENT_BLOCK
from utils.firm import get_escrow_contract, firm_susde_market_contract
from utils.web3_utils import w3, fetch_events_logs_with_retry, call_with_retry


class Firm(Integration):
    def __init__(self):
        super().__init__(
            IntegrationID.FIRM_SUSDE,
            FIRM_SUSDE_DEPLOYMENT_BLOCK,
            Chain.ETHEREUM,
            None,
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        # get user escrow
        escrow_contract = get_escrow_contract(user)
        # get the balance from the escrow
        balance = call_with_retry(
            escrow_contract.functions.balance(),
            block,
        )
        return balance / 1e18

    def get_participants(self) -> list:
        page_size = 1900
        start_block = FIRM_SUSDE_DEPLOYMENT_BLOCK
        target_block = w3.eth.get_block_number()

        all_users = set()
        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            escrow_creations = fetch_events_logs_with_retry(
                f"Inverse Finance FiRM users from {start_block} to {to_block}",
                firm_susde_market_contract.events.CreateEscrow(),
                start_block,
                to_block,
            )
            for escrow_creation in escrow_creations:
                all_users.add(escrow_creation["args"]["user"])
            start_block += page_size

        all_users = list(all_users)
        self.participants = all_users
        return all_users


if __name__ == "__main__":
    firm = Firm()
    participants = firm.get_participants()
    print("participants", participants)
    currentBlock = w3.eth.get_block_number()
    if len(participants) > 0:
        print(firm.get_balance(list(participants)[len(participants) - 1], currentBlock))
