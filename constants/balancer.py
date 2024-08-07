from dataclasses import dataclass
from typing import Dict, Optional

from constants.chains import Chain
from constants.integration_ids import IntegrationID

## If you want to integrate another Balancer Pool, first add it to the IntegrationID enum in integration_ids.py
## Then, add a new entry to the INTEGRATION_CONFIGS dictionary below. Aura integration is optional.
## If the chain is not yet supported, add it to the Chain enum in chains.py and add RPCs to web3_utils.py.


@dataclass
class IntegrationConfig:
    chain: Chain
    start_block: int
    incentivized_token: str
    pool_id: str
    is_composable_pool: bool  # CSP has a different function for getting the BPT supply
    gauge_address: str
    aura_address: str


INTEGRATION_CONFIGS: Dict[IntegrationID, IntegrationConfig] = {
    IntegrationID.BALANCER_FRAXTAL_FRAX_USDE: IntegrationConfig(
        chain=Chain.FRAXTAL,
        start_block=5931687,
        incentivized_token="0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34",
        pool_id="0xa0af0b88796c1aa67e93db89fead2ab7aa3d6747000000000000000000000007",
        is_composable_pool=True,
        gauge_address="0xf99d875Dd868277cf3780f51D69c6E1F8522a1e9",
        aura_address="0x56bA1E88340fD53968f686490519Fb0fBB692a39",
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
