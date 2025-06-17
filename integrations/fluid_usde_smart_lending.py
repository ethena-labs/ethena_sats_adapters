from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from utils.web3_utils import call_with_retry, W3_BY_CHAIN
from utils.fluid import smartLendingResolver_contract
from constants.fluid import USDe
import json

# covers all Fluid smart lending USDE vaults (LP positions)
class FluidIntegration(Integration):

    def __init__(self):
        super().__init__(
            IntegrationID.FLUID_USDE_SMART_LENDING,
            22579344,
            Chain.ETHEREUM,
            [],
            30,
            1,
            None,
            None,
        )
        self.blocknumber_to_usde_smart_lendings = {}

    def get_balance(self, user: str, block: int) -> float:
        balance = 0
        try:
            userPositions = call_with_retry(
                smartLendingResolver_contract.functions.getUserPositions(user), block
            )
            for i in range(len(userPositions)):
                smartLendingEntireData = userPositions[i][0]
                if (smartLendingEntireData[8] == USDe or smartLendingEntireData[9] == USDe): # smartLendingEntireData.token0 or token1 must be USDE
                    
                    userPosition = userPositions[i][1]
                    dexEntireData = smartLendingEntireData[-2] # smartLendingEntireData.dexEntireData
                    userShares = userPosition[2] # userPosition.underlyingShares

                    # For an example walkthrough see fluid_susde_smart.py. using exact same proven flow here

                    # token0PerSupplyShare = dexEntireData[7][-4]
                    # token1PerSupplyShare = dexEntireData[7][-3]
                    userPositionToken0 = userShares * dexEntireData[7][-4] / 1e18
                    userPositionToken1 = userShares * dexEntireData[7][-3] / 1e18

                    if (smartLendingEntireData[8] == USDe): 
                        # token0 at the dex is USDe
                        balance += userPositionToken0
                        # lastStoredPrice = dexEntireData[4][0]
                        userPositionToken1 = userPositionToken1 * 1e54 / dexEntireData[4][0] / 1e27
                        # * 1e6 * numeratorPrecision / denominatorPrecision
                        userPositionToken1 = userPositionToken1 * 1e6 * dexEntireData[2][2] / dexEntireData[2][3]

                        balance += userPositionToken1
                    else:
                        # token1 at the dex is USDe
                        balance += userPositionToken1
                        # lastStoredPrice = dexEntireData[4][0]
                        userPositionToken0 = userPositionToken0 * dexEntireData[4][0] / 1e27
                        # * 1e6 * numeratorPrecision / denominatorPrecision
                        userPositionToken0 = userPositionToken0 * 1e6 * dexEntireData[2][0] / dexEntireData[2][1]
                    
                        balance += userPositionToken0
            return balance / 1e18
        except Exception as e:
            return 0

    def get_participants(self, blocks: list[int] | None) -> set[str]:
        participants = []
        current_block = W3_BY_CHAIN[self.chain]["w3"].eth.get_block_number()

        relevant_smart_lendings = self.get_relevant_smart_lendings(current_block)
        relavantUserPositions = []

        # try:
        #     for smartLending in relevant_smart_lendings:
        #         # Todo: get all users for smart lending address
        # except Exception as e:
        #     print(f"Error: {str(e)}")
        return set(participants)

    def get_relevant_smart_lendings(self, block: int) -> list:
        if block in self.blocknumber_to_usde_smart_lendings:
            return self.blocknumber_to_usde_smart_lendings[block]

        smartLendings = None
        if self.blocknumber_to_usde_smart_lendings != {}:
            smartLendings = call_with_retry(
                    smartLendingResolver_contract.functions.getAllSmartLendingAddresses(), block
                )
            totalSmartLendings = len(smartLendings)
            for block_number in self.blocknumber_to_usde_smart_lendings:
                totalSmartLendings_at_block = len(
                    call_with_retry(
                        smartLendingResolver_contract.functions.getAllSmartLendingAddresses(), block_number
                    )
                )
                if totalSmartLendings == totalSmartLendings_at_block:
                    self.blocknumber_to_usde_smart_lendings[block] = (
                        self.blocknumber_to_usde_smart_lendings[block_number]
                    )
                    return self.blocknumber_to_usde_smart_lendings[block_number]

        if smartLendings is None:
            smartLendings = call_with_retry(
                smartLendingResolver_contract.functions.getAllSmartLendingAddresses(), block
            )

        relevantSmartLendings = []
        for smartLendingAddress in smartLendings:
            smartLendingData = call_with_retry(
                smartLendingResolver_contract.functions.getSmartLendingEntireViewData(smartLendingAddress), block
            )

            if (smartLendingData[8] == USDe or smartLendingData[9] == USDe):
                relevantSmartLendings.append(smartLendingAddress)
        self.blocknumber_to_usde_smart_lendings[block] = relevantSmartLendings
        return relevantSmartLendings


if __name__ == "__main__":
    example_integration = FluidIntegration()
    print("getting relevant smart lendings")
    print(example_integration.get_relevant_smart_lendings(22723719))

    print("\n\n\ngetting participants")
    print(example_integration.get_participants(22723719))

    print("\n\n\n getting balance")
    print(
        example_integration.get_balance(
            # should have 1029582
            "0x0A20507fC1a33CBd15C5FD5197b259Ca644e7769", 22723719
        )
    )
