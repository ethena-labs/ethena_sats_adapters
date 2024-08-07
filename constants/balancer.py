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
    gauge_address: str
    aura_address: Optional[str] = None


INTEGRATION_CONFIGS: Dict[IntegrationID, IntegrationConfig] = {
    IntegrationID.BALANCER_FRAXTAL_FRAX_USDE: IntegrationConfig(
        chain=Chain.FRAXTAL,
        start_block=5931687,
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
