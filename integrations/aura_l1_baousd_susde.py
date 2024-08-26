
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# L1 baoUSD-sUSDe pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=224,
        start_block=20_433_615,
        crv_rewards_address="0xD34793BF42D922B04E7e53253F7195725A4a7E9d",
        chain=Chain.ETHEREUM
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
