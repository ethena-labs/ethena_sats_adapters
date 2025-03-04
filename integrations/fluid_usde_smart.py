from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from utils.web3_utils import call_with_retry, W3_BY_CHAIN
from utils.fluid import (
    vaultResolver_contract,
    vaultPositionResolver_contract,
    dexResolver_contract,
)
from constants.fluid import USDe
import json

# covers all Fluid smart col USDE vaults (LP positions)
class FluidIntegration(Integration):

    def __init__(self):
        super().__init__(
            IntegrationID.FLUID_USDE_SMART,
            21673938,
            Chain.ETHEREUM,
            [],
            30,
            1,
            None,
            None,
        )
        self.blocknumber_to_usdeVaults = {}

    def get_balance(self, user: str, block: int) -> float:
        balance = 0
        try:
            userPositions, vaultEntireDatas = call_with_retry(
                vaultResolver_contract.functions.positionsByUser(user), block
            )
            dexEntireDatas = {}
            for i in range(len(userPositions)):
                if (vaultEntireDatas[i][3][8][0] == USDe or vaultEntireDatas[i][3][8][1] == USDe) and (vaultEntireDatas[i][1]): # ONLY smart col types
                    # underlying dex as supply token in the vault
                    # fetching the dex state to get the shares to tokens ratio
                    dexAddress = vaultEntireDatas[i][3][6]
                    if dexAddress not in dexEntireDatas:
                        dexEntireDatas[dexAddress] = (
                            dexResolver_contract.functions.getDexEntireData(dexAddress).call(
                                block_identifier=block
                            )
                        )
                    
                    # For an example walkthrough see fluid_susde_smart.py

                    # userShares =  userPositions[i][9]
                    # token0PerSupplyShare = dexEntireDatas[dexAddress][7][-4]
                    # token1PerSupplyShare = dexEntireDatas[dexAddress][7][-3]
                    userPositionToken0 = userPositions[i][9] * dexEntireDatas[dexAddress][7][-4] / 1e18
                    userPositionToken1 = userPositions[i][9] * dexEntireDatas[dexAddress][7][-3] / 1e18

                    if (vaultEntireDatas[i][3][8][0] == USDe): 
                        # token0 at the dex is USDe
                        balance += userPositionToken0
                        # lastStoredPrice = dexEntireDatas[dexAddress][4][0]
                        userPositionToken1 = userPositionToken1 * 1e54 / dexEntireDatas[dexAddress][4][0] / 1e27
                        # * 1e6 * numeratorPrecision / denominatorPrecision
                        userPositionToken1 = userPositionToken1 * 1e6 * dexEntireDatas[dexAddress][2][2] / dexEntireDatas[dexAddress][2][3]

                        balance += userPositionToken1
                    else:
                        # token1 at the dex is USDe
                        balance += userPositionToken1
                        # lastStoredPrice = dexEntireDatas[dexAddress][4][0]
                        userPositionToken0 = userPositionToken0 * dexEntireDatas[dexAddress][4][0] / 1e27
                        # * 1e6 * numeratorPrecision / denominatorPrecision
                        userPositionToken0 = userPositionToken0 * 1e6 * dexEntireDatas[dexAddress][2][0] / dexEntireDatas[dexAddress][2][1]
                    
                        balance += userPositionToken1
            return balance / 1e18
        except Exception as e:
            return 0

    def get_participants(self, blocks: list[int] | None) -> set[str]:
        participants = []
        current_block = W3_BY_CHAIN[self.chain]["w3"].eth.get_block_number()

        relevant_vaults = self.get_relevant_vaults(current_block)
        relavantUserPositions = []

        try:
            for vault in relevant_vaults:
                relavantUserPositions += call_with_retry(
                    vaultPositionResolver_contract.functions.getAllVaultPositions(
                        vault
                    ),
                    current_block,
                )
            for userPosition in relavantUserPositions:
                owner = userPosition[1]
                if owner not in participants:
                    participants.append(owner)
        except Exception as e:
            print(f"Error: {str(e)}")
        return set(participants)

    def get_relevant_vaults(self, block: int) -> list:
        if block in self.blocknumber_to_usdeVaults:
            return self.blocknumber_to_usdeVaults[block]

        if self.blocknumber_to_usdeVaults != {}:
            totalVaults = call_with_retry(
                vaultResolver_contract.functions.getTotalVaults(), block
            )
            for block_number in self.blocknumber_to_usdeVaults:
                totalVaults_at_block = call_with_retry(
                    vaultResolver_contract.functions.getTotalVaults(), block_number
                )
                if totalVaults == totalVaults_at_block:
                    self.blocknumber_to_usdeVaults[block] = (
                        self.blocknumber_to_usdeVaults[block_number]
                    )
                    return self.blocknumber_to_usdeVaults[block_number]

        vaults = call_with_retry(
            vaultResolver_contract.functions.getAllVaultsAddresses(), block
        )
        relevantVaults = []
        for vaultAddress in vaults:
            vaultData = call_with_retry(
                vaultResolver_contract.functions.getVaultEntireData(vaultAddress), block
            )
            if (vaultData[3][8][0] == USDe or vaultData[3][8][1] == USDe) and (vaultData[1]): # ONLY smart col types
                relevantVaults.append(vaultAddress)
        self.blocknumber_to_usdeVaults[block] = relevantVaults
        return relevantVaults


if __name__ == "__main__":
    example_integration = FluidIntegration()
    print("getting relevant vaults")
    print(example_integration.get_relevant_vaults(21745303))

    print("\n\n\ngetting participants")
    print(example_integration.get_participants(None))

    print("\n\n\n getting balance")
    print(
        example_integration.get_balance(
            # should be ~669k USDE
            "0xDB611d682cb1ad72fcBACd944a8a6e2606a6d158", 21745303
        )
    )
