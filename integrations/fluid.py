from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.web3_utils import call_with_retry, W3_BY_CHAIN
from utils.fluid import vaultResolver_contract, vaultFactory_contract, vaultPositionResolver_contract
from constants.integration_token import Token

class FluidIntegration(
    Integration
):
    def __init__(self):
        super().__init__(
            IntegrationID.FLUID,
            21016131,
            Chain.ETHEREUM,
            None,
            5,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        balance = 0
        relevant_vaults = self.get_relevant_vaults(block)
        for vault in relevant_vaults:
            allUserPositions = call_with_retry(vaultPositionResolver_contract.functions.getAllVaultPositions(vault), block)
            for userPosition in allUserPositions:
                if userPosition[1] == user:
                    balance += userPosition[2]
        return balance/1e18

    def get_participants(self) -> list:
        participants = []
        current_block = W3_BY_CHAIN[self.chain]["w3"].eth.get_block_number()

        relevant_vaults = self.get_relevant_vaults(current_block)
        relavantNfts = []

        for vault in relevant_vaults:
            relavantNfts += call_with_retry(vaultPositionResolver_contract.functions.getAllVaultNftIds(vault), current_block)

        try:
            current_block = W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.get_block_number()
            for i in relavantNfts:
                owner = call_with_retry(vaultFactory_contract.functions.ownerOf(i), current_block)
                if owner not in participants:
                    participants.append(owner)
        except Exception as e:
            print(f"Error: {str(e)}")
        return participants
    
    def get_relevant_vaults(self, block: int) -> list:
        vaults = call_with_retry(vaultResolver_contract.functions.getAllVaultsAddresses(), block)
        for vaultAddress in vaults:
            supplyTokenOfVault = (call_with_retry(vaultResolver_contract.functions.getVaultEntireData(vaultAddress), block))[3][8][0]
            if supplyTokenOfVault == Token.SUSDE:
                vaults.append(vaultAddress)
        return vaults


if __name__ == "__main__":
    example_integration = FluidIntegration()
    print(example_integration.get_relevant_vaults(21088189))
    print(example_integration.get_participants())
    print(
        example_integration.get_balance("0x169dC0999f4dD957EbcB68a7A8AFfe87c57C4faE", 21079685)
    )