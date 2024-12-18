from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

from constants.chains import Chain
from integrations.integration_ids import IntegrationID

## If you want to integrate another Balancer Pool, first add it to the IntegrationID enum in integration_ids.py
## Then, add a new entry to the INTEGRATION_CONFIGS dictionary below. Aura integration is optional.
## If the chain is not yet supported, add it to the Chain enum in chains.py and add RPCs to web3_utils.py.


# Addresses for Ethena tokens are the same across L2 chains (except ZKsync)
class Token(Enum):
    USDE = "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"
    SUSDE = "0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2"
    ENA = "0x58538e6A46E07434d7E7375Bc268D3cb839C0133"


@dataclass
class IntegrationConfig:
    chain: Chain
    start_block: int
    incentivized_token: str
    incentivized_token_decimals: int
    pool_id: str
    gauge_address: str
    aura_address: str
    has_preminted_bpts: bool = (
        False  # CSPs have a different function for getting the BPT supply
    )


INTEGRATION_CONFIGS: Dict[IntegrationID, IntegrationConfig] = {
    IntegrationID.BALANCER_FRAXTAL_FRAX_USDE: IntegrationConfig(
        chain=Chain.FRAXTAL,
        start_block=5931687,
        incentivized_token=Token.USDE.value,
        incentivized_token_decimals=18,
        pool_id="0xa0af0b88796c1aa67e93db89fead2ab7aa3d6747000000000000000000000007",
        gauge_address="0xf99d875Dd868277cf3780f51D69c6E1F8522a1e9",
        aura_address="0x56bA1E88340fD53968f686490519Fb0fBB692a39",
        has_preminted_bpts=True,
    ),
    IntegrationID.BALANCER_ARBITRUM_GHO_USDE: IntegrationConfig(
        chain=Chain.ARBITRUM,
        start_block=225688025,
        incentivized_token=Token.USDE.value,
        incentivized_token_decimals=18,
        pool_id="0x2b783cd37774bb77d387d35683e8388937712f0a00020000000000000000056b",
        gauge_address="0xf2d151c40C18d8097AAa5157eE8f447CBe217269",
        aura_address="0x106398c0a78AE85F501FEE16d53A81401469b9B8",
    ),
    IntegrationID.BALANCER_ARBITRUM_WAGHO_USDE: IntegrationConfig(
        chain=Chain.ARBITRUM,
        start_block=245277323,
        incentivized_token=Token.USDE.value,
        incentivized_token_decimals=18,
        pool_id="0x38161e9efb8de52d00a1eb0f773223fd28fdd7c20002000000000000000005a0",
        gauge_address="0xcfab2efef3affdd158568dc896115eac26b3c498",
        aura_address="0x8f2c4c4ad0b45a3c740e7f7fbc5a106659adeee7",
    ),
    IntegrationID.BALANCER_ARBITRUM_GYD_SUSDE: IntegrationConfig(
        chain=Chain.ARBITRUM,
        start_block=240466292,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_id="0xdeeaf8b0a8cf26217261b813e085418c7dd8f1ee00020000000000000000058f",
        gauge_address="0xdEC026525FE4FEF54857bCF551aEA97aBc24A673",
        aura_address="0x2d7cFe43BcDf10137924a20445B763Fb40E5871c",
    ),
    IntegrationID.BALANCER_ARBITRUM_SUSDE_SFRAX: IntegrationConfig(
        chain=Chain.ARBITRUM,
        start_block=197330091,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_id="0x59743f1812bb85db83e9e4ee061d124aaa64290000000000000000000000052b",
        gauge_address="0x4b8858a8E42f406B4dC2eCB8D48B5cf0021035c8",
        aura_address="0x0a6a427867a3274909A04276cB5589AE8Cc2dfc7",
        has_preminted_bpts=True,
    ),
    IntegrationID.BALANCER_ARBITRUM_SUSDE_USDC: IntegrationConfig(
        chain=Chain.ARBITRUM,
        start_block=197316005,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_id="0x2f0cdf8596be980ef24924ca7bf54e630ca526b2000000000000000000000529",
        gauge_address="0xe9801a0fa08acf9140ba3a347a8c6048ff9eab7c",
        aura_address="0x043A59D13884DddCa18b99C3C184C29aAd973b35",
        has_preminted_bpts=True,
    ),
    IntegrationID.BALANCER_ETHEREUM_WSTETH_SUSDE: IntegrationConfig(
        chain=Chain.ETHEREUM,
        start_block=20005052,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_id="0xa8210885430aaa333c9f0d66ab5d0c312bed5e43000200000000000000000692",
        gauge_address="0xbd00c7cbe59dddbd784c899ac173b7ba514b9997",
        aura_address="0x99d9e4d3078f7c9c5b792999749290a54fb87257",
    ),
    IntegrationID.BALANCER_ETHEREUM_BAOUSD_SUSDE: IntegrationConfig(
        chain=Chain.ETHEREUM,
        start_block=20169334,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_id="0x79af734562f741946566d5126bbded4cb699e35500000000000000000000069f",
        gauge_address="0xf91ba601c53f831869da4aceaaec11c479413972",
        aura_address="0xd34793bf42d922b04e7e53253f7195725a4a7e9d",
        has_preminted_bpts=True,
    ),
    IntegrationID.BALANCER_ETHEREUM_SUSDE_USDC: IntegrationConfig(
        chain=Chain.ETHEREUM,
        start_block=19663564,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_id="0xb819feef8f0fcdc268afe14162983a69f6bf179e000000000000000000000689",
        gauge_address="0x84f7f5cd2218f31b750e7009bb6fd34e0b945dac",
        aura_address="0x4b87dcff2f45535775a9564229119dca5e697a10",
        has_preminted_bpts=True,
    ),
    IntegrationID.BALANCER_ETHEREUM_SUSDE_GYD: IntegrationConfig(
        chain=Chain.ETHEREUM,
        start_block=20569775,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_id="0x8d93b853849b9884e2bb413444ec23eb5366ee910002000000000000000006b3",
        gauge_address="0x146b6030E6d6a6398B918E9854652a71C9537180",
        aura_address="0x1f2b312c30b08c1957bd3ada616e77bc7bff51ff",
    ),
    IntegrationID.BALANCER_FRAXTAL_SFRAX_SDAI_SUSDE: IntegrationConfig(
        chain=Chain.FRAXTAL,
        start_block=5931675,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_id="0x33251abecb0364df98a27a8d5d7b5ccddc774c42000000000000000000000008",
        gauge_address="0x275e8514b83479f526673327b279753abc666a05",
        aura_address="0x8bb2303ab3ff8bcb1833b71ca14fde75cb88d0b8",
        has_preminted_bpts=True,
    ),
    IntegrationID.BALANCER_FRAXTAL_FRAX_USDE_DAI_USDT_USDC: IntegrationConfig(
        chain=Chain.FRAXTAL,
        start_block=6859850,
        incentivized_token=Token.USDE.value,
        incentivized_token_decimals=18,
        pool_id="0x760b30eb4be3ccd840e91183e33e2953c6a31253000000000000000000000005",
        gauge_address="0x982653b874b059871a46f66120c69503fe391979",
        aura_address="0x5a1e521e700d684323886346a2c782febcc0ea4b",
        has_preminted_bpts=True,
    ),
}


def get_integration_config(
    integration_id: IntegrationID,
) -> Optional[IntegrationConfig]:
    return INTEGRATION_CONFIGS.get(integration_id)


AURA_VOTER_PROXY = {
    Chain.FRAXTAL: "0xC181Edc719480bd089b94647c2Dc504e2700a2B0",
}

BALANCER_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
