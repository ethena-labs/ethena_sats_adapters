from integrations.integration_ids import IntegrationID
from integrations.integration import Integration
from utils.balancer import (
    get_vault_pool_token_balance,
    get_potential_token_holders,
    get_user_balance,
    get_bpt_supply,
)
from constants.balancer import INTEGRATION_CONFIGS


class BalancerIntegration(Integration):
    def __init__(self, integration_id: IntegrationID):
        config = INTEGRATION_CONFIGS.get(integration_id)
        if not config:
            raise ValueError(
                f"No configuration found for integration ID: {integration_id}"
            )

        super().__init__(
            integration_id,
            config.start_block,
            config.chain,
            None,
            20,
            1,
            None,
            None,
        )

        self.pool_id = config.pool_id
        self.has_preminted_bpts = config.has_preminted_bpts
        self.gauge_address = config.gauge_address
        self.aura_address = config.aura_address
        self.incentivized_token = config.incentivized_token
        self.incentivized_token_decimals = config.incentivized_token_decimals

    def get_balance(self, user: str, block: int) -> float:
        """
        Retrieve the balance of the user in the incentivized Ethena token.

        This method calculates the user's token balance based on the share of Balancer Pool Tokens (BPTs)
        staked either directly in Balancer gauges or via Aura Finance.
        """
        gauge_balance = get_user_balance(self.chain, user, self.gauge_address, block)
        aura_balance = get_user_balance(self.chain, user, self.aura_address, block)

        bpt_address = self.pool_id[:42]
        bpt_supply = get_bpt_supply(
            self.chain, bpt_address, self.has_preminted_bpts, block
        )

        user_balance = gauge_balance + aura_balance

        incentivized_token_balance = get_vault_pool_token_balance(
            self.chain, self.pool_id, self.incentivized_token, block
        )

        user_share = user_balance / bpt_supply

        return (
            user_share
            * incentivized_token_balance
            / pow(10, self.incentivized_token_decimals)
        )

    def get_participants(self) -> list:
        """
        Retrieve the set of all unique participants who might have staked Balancer Pool Tokens (BPTs).

        This method identifies all addresses that have staked their BPT either directly
        in Balancer gauges or via Aura Finance. Non-staked BPT holders are not included.
        """
        gauge_holders = get_potential_token_holders(
            self.chain, self.gauge_address, self.start_block
        )
        aura_holders = get_potential_token_holders(
            self.chain, self.aura_address, self.start_block
        )

        self.participants = set(aura_holders + gauge_holders)
        return self.participants


if __name__ == "__main__":
    balancer = BalancerIntegration(IntegrationID.BALANCER_FRAXTAL_FRAX_USDE)
    # print(balancer.get_participants())
    participants = {
        "0x58d70BFa5B7dEf2B44c2B6c6e1F50bed4950B4D6",
        "0x5836130b9f34deeb78C7642f37E921F913E4C3d6",
        "0xDE609fb3ef5875bE6cD5F881F17aF17E5FAE16cd",
        "0xFe077981C40B01E0f2CD28633799C87F951Fa954",
        "0xBcA4D68BE543dCEFb1a8bcCb519503f9ba3f2026",
        "0x2E2aFAFbeEaA08d6883dCdEBEe84A2d623a9CEee",
        "0xB439b0844D0D9aF237FF37dc2379f07B6CD06171",
        "0x16E1bc23C2210Ed6C8410e3c6Ec0FD8C0B5662Da",
        "0x60b1708e496f33EFb9198Fe5219656f31665d16c",
        "0x7caec00E024BbDe0dCdaEED9c9407bAf88FDC65c",
        "0x9C1DF238A1b1B1F5E3bC5C046201B253D8Bf9E3c",
        "0x1CaadD7BbAD2eEDb593bb808Db4Af1a678AF560b",
        "0xb541765F540447646A9545E0A4800A0Bacf9E13D",
        "0x97a1CA841B4792068932D4224681f6F6fa22C549",
        "0x69344717556C64DC49A2Ba36267A04efAcF34d27",
        "0x584358236b7bcd791077843B8a7E5c8419b51c86",
        "0x650036B83283656BCa3a4D11671E3DD4229B5720",
        "0x8e5D2f8A445dD6812e907BCB0fB4633656BcB8cd",
        "0x5452E6ABbC7bCB9e0907A3f8f24434CbaF438bA4",
        "0x72292f8183dAD15DAe55377321d29F1053d1603F",
        "0x18D62A25e399CEF8F8FBf36C1a3055657f6E5775",
        "0x73E4a6BD123aBf43Ef1da93C214BE8DA0dF3b20a",
        "0x576159e8003e74cbDb5b2274CfC4418BB60cD0d8",
        "0xDcc5b9BA5aB98DC38477831Ff359d81f911423eb",
        "0x35341d0F2eAe4aE3782c4F7a08C86f7717fD0839",
        "0x75C108dF63381E5b2FAe62d610D79A8915911AA8",
        "0x653181142dC87D1bc4a1b7849604D4ba510a4A3d",
        "0xd476c2dB017a1e8be6D2ccbF6E00BEE544aaa316",
        "0xF4E7e39411E60C2B9AECd6C92482e1980bbB3A4D",
        "0xeeDb07ae31191e8E803685887Bf653754f2f6F52",
        "0x1e892233459C4F96B9bafD13947f75EbF96410Ae",
        "0x2cFb075E8FC0D99837653629B0A3d527f0769a1A",
        "0x90e06d2d9705c181Bad2A4e7c3DcA13631a6f479",
        "0x09Fa38EBa245bb68354B8950FA2fe71f02863393",
        "0xE059A37d87C49503B283a2F7A3A5d4B652ff7351",
        "0x05747fc55e8156F2337a5e525f5c5818BD8f195F",
        "0x61EF43A10d4bc127c961D89e122595d85e87e2C8",
        "0x4A380643690dc94e0182826Dc97bAAD4E6686646",
        "0x4B298f807E0449C6Eb0320773dc4d3fb1BDf7B25",
        "0xc87e3788764823CEDdD132CA2E697767de5ed4de",
        "0x4CB01b6672bc750821af952ec5A2447fC90195b1",
        "0x4b08d2f583C119902ef5599BC30396F83865Fec8",
        "0x854B004700885A61107B458f11eCC169A019b764",
        "0x4334703B0B74E2045926f82F4158A103fCE1Df4f",
        "0xf0f74277C46eBec6B6C9678C9B3b8637B893918D",
        "0xe3Be0Baae3d4928D3e2E7724d4bf188003C56EBF",
        "0x82495AFEa7a975F637e68eb5f9afF15071d35BB0",
        "0xc018C33B4Db79144e6B6D3220AB6c53565BA1931",
        "0x5EB476bFD8C1a9Ba7A9663543a6686193b42600c",
        "0xC0fC2fA4629A1a23Ded78193ac16dfe6FFc05269",
    }
    for participant in participants:
        print(participant, balancer.get_balance(participant, "latest"))
    # print(balancer.get_balance(list(participants)[0], "latest"))
