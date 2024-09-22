import json
from constants.chains import Chain
from constants.dyad import DYAD_NOTE_ADDRESS, DYAD_NOTE_DEPLOYMENT_BLOCK, DYAD_SUSDE_VAULT_ADDRESS, DYAD_SUSDE_VAULT_DEPLOYMENT_BLOCK, DYAD_VAULT_MANAGER_ADDRESS
from models.integration import Integration
from utils.web3_utils import w3, call_with_retry, fetch_events_logs_with_retry

page_size = 100000

from constants.integration_ids import IntegrationID

with open("abi/dyad_vault.json") as f:
    dyad_vault_abi = json.load(f)

with open("abi/dyad_vaultmanager.json") as f:
    dyad_vaultmanager_abi = json.load(f)

with open("abi/dyad_note.json") as f:
    dyad_note_abi = json.load(f)

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
            address=w3.to_checksum_address(DYAD_SUSDE_VAULT_ADDRESS), 
            abi=dyad_vault_abi
        )
        return call_with_retry(vault.functions.balanceOf(w3.to_checksum_address(user)), block)

    def get_participants(self) -> list:
        
        all_notes = set()
        all_users = set()

        start_block = DYAD_SUSDE_VAULT_DEPLOYMENT_BLOCK

        target_block = w3.eth.get_block_number()

        vault_manager = w3.eth.contract(
            address=w3.to_checksum_address(DYAD_VAULT_MANAGER_ADDRESS), 
            abi=dyad_vaultmanager_abi
        )

        notes = w3.eth.contract(
            address=w3.to_checksum_address(DYAD_NOTE_ADDRESS),
            abi=dyad_note_abi
        )

        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            print(f"Getting sUSDe enabled notes from {start_block} to {to_block}")

            vault_addeds = fetch_events_logs_with_retry(
                "Vault Added",
                vault_manager.events.Added(),
                start_block,
                to_block
            )

            for vault in vault_addeds:
                if vault.args.vault == w3.to_checksum_address(DYAD_SUSDE_VAULT_ADDRESS):
                    print(vault.args.id, ": found sUSDe vault")
                    all_notes.add(vault.args.id)
            start_block += page_size

        start_block = DYAD_NOTE_DEPLOYMENT_BLOCK

        print(f'{list(all_notes)}')

        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)

            print(f"Getting sUSDe enabled notes owners from {start_block} to {to_block}")

            note_transfers = fetch_events_logs_with_retry(
                "Note Transferred",
                notes.events.Transfer(),
                start_block,
                to_block,
            )

            for transfer in note_transfers:
                if transfer.args.tokenId in all_notes:
                    all_users.add(transfer.args.to)
            
            start_block += page_size
            
        return list(all_users)
    
if __name__ == "__main__":
    example_integration = DyadIntegration(IntegrationID.DYAD_SUSDE_VAULT)
    current_block = w3.eth.get_block_number()

    participants = example_integration.get_participants()
    print("Found Dyad Participants:")
    print(participants)

    print("Balances of Participants:")
    for participant in participants:
        print(f'address: {participant:} {example_integration.get_balance(participant, current_block)}')
