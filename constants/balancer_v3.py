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
    pool_address: str
    gauge_address: str | None
    aura_address: str | None


INTEGRATION_CONFIGS: Dict[IntegrationID, IntegrationConfig] = {
    IntegrationID.BALANCER_FRAXTAL_FRAX_USDE_DAI_USDT_USDC: IntegrationConfig(
        chain=Chain.FRAXTAL,
        start_block=6859850,
        incentivized_token=Token.USDE.value,
        pool_address="0x760b30eb4be3ccd840e91183e33e2953c6a31253000000000000000000000005",
        gauge_address="0x982653b874b059871a46f66120c69503fe391979",
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
