
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# Arbitrum sUSDe/USDC pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=59,
        start_block=204_280_161,
        crv_rewards_address="0x043A59D13884DddCa18b99C3C184C29aAd973b35",
        chain=Chain.ARBITRUM
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
