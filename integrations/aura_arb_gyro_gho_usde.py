
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# Arbitrum Gyroscope ECLP GHO/USDe pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=75,
        start_block=230_683_522,
        crv_rewards_address="0x106398c0a78AE85F501FEE16d53A81401469b9B8",
        chain=Chain.ARBITRUM
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
