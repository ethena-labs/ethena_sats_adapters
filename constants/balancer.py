from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

from constants.chains import Chain
from constants.integration_ids import IntegrationID

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
        pool_id="0xa0af0b88796c1aa67e93db89fead2ab7aa3d6747000000000000000000000007",
        gauge_address="0xf99d875Dd868277cf3780f51D69c6E1F8522a1e9",
        aura_address="0x56bA1E88340fD53968f686490519Fb0fBB692a39",
        has_preminted_bpts=True,
    ),
    IntegrationID.BALANCER_ARBITRUM_GHO_USDE.value: IntegrationConfig(
        chain=Chain.ARBITRUM,
        start_block=225688025,
        incentivized_token=Token.USDE.value,
        pool_id="0x2b783cd37774bb77d387d35683e8388937712f0a00020000000000000000056b",
        gauge_address="0xf2d151c40C18d8097AAa5157eE8f447CBe217269",
        aura_address="0x106398c0a78AE85F501FEE16d53A81401469b9B8",
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
