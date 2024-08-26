
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# Arbitrum Gyroscope ECLP sUSDe/GYD pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=82,
        start_block=244_761_472,
        crv_rewards_address="0x2d7cFe43BcDf10137924a20445B763Fb40E5871c",
        chain=Chain.ARBITRUM
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
