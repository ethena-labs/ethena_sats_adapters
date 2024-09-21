import json
from constants.chains import Chain
from constants.dyad import DYAD_SUSDE_VAULT_ADDRESS, DYAD_SUSDE_VAULT_DEPLOYMENT_BLOCK, DYAD_VAULT_MANAGER_ADDRESS
from models.integration import Integration
from utils.web3_utils import w3, call_with_retry, fetch_events_logs_with_retry
import logging

page_size = 100

from constants.integration_ids import IntegrationID

with open("abi/dyad_vault.json") as f:
    dyad_vault_abi = json.load(f)

with open("abi/dyad_vaultmanager.json") as f:
    dyad_vaultmanager_abi = json.load(f)

class DyadIntegration(Integration):
    def __init__(self, integration_id: IntegrationID):
        super().__init__(
            integration_id,
            DYAD_SUSDE_VAULT_DEPLOYMENT_BLOCK,
            Chain.ETHEREUM,
            None
        )

    def get_balance(self, user: str, block: int) -> float:
        vault = w3.eth.contract(
            address=DYAD_SUSDE_VAULT_ADDRESS, abi=dyad_vault_abi
        ),
        return call_with_retry(vault.balanceOf(user), block)

    def get_participants(self) -> list:
        all_users = set()

        start_block = DYAD_SUSDE_VAULT_DEPLOYMENT_BLOCK

        target_block = w3.eth.get_block_number()

        vault_manager = w3.eth.contract(
            address=DYAD_VAULT_MANAGER_ADDRESS, abi=dyad_vaultmanager_abi
        ),

        print(vault_manager)

        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            event_label = f"Getting sUSDe enabled notes from {start_block} to {to_block}"

            vault_addeds = fetch_events_logs_with_retry(
                "Vault Added",
                vault_manager.events.Added(),
                start_block,
                to_block,
            )

            for vault in vault_addeds:
                print(event_label, ": found", vault, "transfers")
            start_block += page_size
        return all_users
    
if __name__ == "__main__":
    example_integration = DyadIntegration(IntegrationID.DYAD_SUSDE_VAULT)
    current_block = w3.eth.get_block_number()

    print("Found Dyad Participants:")
    print(example_integration.get_participants())
    print("Found Balance of First Participant:")
    print(example_integration.get_balance(list(example_integration.participants)[0], current_block))
