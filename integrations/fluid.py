from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.web3_utils import call_with_retry, W3_BY_CHAIN
from utils.fluid import vaultResolver_contract, vaultFactory_contract, vaultPositionResolver_contract
from constants.fluid import susde
import json

class FluidIntegration(
    Integration
):
    def __init__(self):
        super().__init__(
            IntegrationID.FLUID,
            21016131,
            Chain.ETHEREUM,
            None,
            20,
            1,
            None,
            None,
        )

    def get_balance(self, user: str, block: int) -> float:
        balance = 0
        try:
            userPositions, vaultEntireDatas = call_with_retry(vaultResolver_contract.functions.positionsByUser(user), block)
            for userPosition in userPositions:
                if vaultEntireDatas[0][3][8][0] != susde:
                    continue
                balance += userPosition[9]
            return balance/1e18
        except Exception as e:
            return 0


    def get_participants(self) -> list:
        participants = []
        current_block = W3_BY_CHAIN[self.chain]["w3"].eth.get_block_number()

        relevant_vaults = self.get_relevant_vaults(current_block)
        relavantNfts = []

        for vault in relevant_vaults:
            relavantNfts += call_with_retry(vaultPositionResolver_contract.functions.getAllVaultNftIds(vault), current_block)

        try:
            current_block = W3_BY_CHAIN[Chain.ETHEREUM]["w3"].eth.get_block_number()
            total_nfts = call_with_retry(vaultResolver_contract.functions.totalPositions(), current_block)
            for i in relavantNfts:
                owner = call_with_retry(vaultFactory_contract.functions.ownerOf(i), current_block)
                if owner not in participants:
                    participants.append(owner)
        except Exception as e:
            print(f"Error: {str(e)}")
        return participants
    
    def get_relevant_vaults(self, block: int) -> list:
        vaults = []
        totalVaults = call_with_retry(vaultFactory_contract.functions.totalVaults(), block)
        for i in range(1, totalVaults + 1):
            print(i)
            vaultAddress = call_with_retry(vaultFactory_contract.functions.getVaultAddress(i), block)
            supplyTokenOfVault = (call_with_retry(vaultResolver_contract.functions.getVaultEntireData(vaultAddress), block))[3][8][0]
            print(supplyTokenOfVault)
            if supplyTokenOfVault == susde:
                vaults.append(vaultAddress)
                print(vaults)
        return vaults


if __name__ == "__main__":
    example_integration = FluidIntegration()
    # print(example_integration.get_relevant_vaults(21088189))
    # print(example_integration.get_participants())
    print(
        example_integration.get_balance("0x169dC0999f4dD957EbcB68a7A8AFfe87c57C4faE", 21079685)
    )