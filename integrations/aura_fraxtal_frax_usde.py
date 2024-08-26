
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# Fraxtal Network FRAX/USDe pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=3,
        start_block=7_002_832,
        crv_rewards_address="0x56bA1E88340fD53968f686490519Fb0fBB692a39",
        chain=Chain.FRAXTAL
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
