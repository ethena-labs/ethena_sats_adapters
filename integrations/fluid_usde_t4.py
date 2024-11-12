from constants.chains import Chain
from constants.integration_ids import IntegrationID
from models.integration import Integration
from utils.web3_utils import call_with_retry, W3_BY_CHAIN
from utils.fluid import vaultResolver_contract, vaultPositionResolver_contract, dexResolver_contract
from constants.fluid import USDe
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
            30,
            1,
            None,
            None,
        )
        self.relevant_vaults = ["0x1B4EC865915872AEc7A30423fdA2584C9fa894C5"]

    def get_balance(self, user: str, block: int) -> float:
        balance = 0
        try:
            userPositions, vaultEntireDatas = call_with_retry(vaultResolver_contract.functions.positionsByUser(user), block)
            dexStates = {}
            for i in range(len(userPositions)):
                if vaultEntireDatas[i][3][8][0] == USDe and userPositions[i][10] == 40000:
                    # underlying dex as supply token in the vault
                    dexAddress = vaultEntireDatas[i][3][6]
                    if dexAddress not in dexStates:
                        dexStates[dexAddress] = dexResolver_contract.functions.getDexState(dexAddress).call(block_identifier=block)
                    # fetching the dex state to get the shares to tokens ratio
                    token0PerSupplyShare = dexStates[dexAddress][-4] 
                    balance += userPositions[i][9] * token0PerSupplyShare
            return balance/1e18
        except Exception as e:
            return 0

    def get_participants(self) -> list:
        participants = []
        current_block = W3_BY_CHAIN[self.chain]["w3"].eth.get_block_number()
        relavantUserPositions = []


        try:
            for vault in self.relevant_vaults:
                relavantUserPositions += call_with_retry(vaultPositionResolver_contract.functions.getAllVaultPositions(vault), current_block)
            for userPosition in relavantUserPositions:
                owner = userPosition[1]
                if owner not in participants:
                    participants.append(owner)
        except Exception as e:
            print(f"Error: {str(e)}")
        return participants


if __name__ == "__main__":
    example_integration = FluidIntegration()

    print("\n\n\ngetting participants")
    print(example_integration.get_participants())

    print("\n\n\n getting balance")
    print(
        example_integration.get_balance("0xEb54fC872F70A4B7addb34C331DeC3fDf9a329de", 21151876)
    )