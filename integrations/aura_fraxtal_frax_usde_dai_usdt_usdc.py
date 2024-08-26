
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# Fraxtal Network FRAX/USDe/DAI/USDT/USDC pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=1,
        start_block=7_002_832,
        crv_rewards_address="0x5A1E521e700d684323886346A2c782FeBCc0EA4B",
        chain=Chain.FRAXTAL
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
