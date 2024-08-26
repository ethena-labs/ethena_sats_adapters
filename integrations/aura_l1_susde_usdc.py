
from constants.chains import Chain
from utils.aura import AuraFinanceIntegration 


# L1 sUSDe/USDC pool
if __name__ == "__main__":
    integration = AuraFinanceIntegration(
        pool_id=208,
        start_block=19_769_205,
        crv_rewards_address="0x4B87DCFF2F45535775a9564229119dca5e697A10",
        chain=Chain.ETHEREUM
    )
    print(integration.get_participants())
    print(integration.get_balance(list(integration.participants)[0], "latest"))
