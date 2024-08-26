
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# Fraxtal Network sFRAX/sDAI/sUSDe pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=4,
        start_block=7_002_832,
        crv_rewards_address="0x8bb2303Ab3FF8BCb1833B71ca14FdE75Cb88d0B8",
        chain=Chain.FRAXTAL
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
