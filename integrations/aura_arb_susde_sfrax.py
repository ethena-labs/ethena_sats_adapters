
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# Arbitrum sUSDe/sFRAX pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=58,
        start_block=201_668_067,
        crv_rewards_address="0x0a6a427867a3274909A04276cB5589AE8Cc2dfc7",
        chain=Chain.ARBITRUM
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
