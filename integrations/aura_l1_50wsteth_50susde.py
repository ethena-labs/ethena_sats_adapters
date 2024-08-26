
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# L1 50wstETH/50sUSDe pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=220,
        start_block=20_369_904,
        crv_rewards_address="0x99D9e4D3078f7C9c5b792999749290A54fB87257",
        chain=Chain.ETHEREUM
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
