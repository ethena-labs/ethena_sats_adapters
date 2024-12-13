from dataclasses import dataclass
from typing import Dict, Optional

from constants.chains import Chain
from constants.balancer import Token
from integrations.integration_ids import IntegrationID

## If you want to integrate another Balancer Pool, first add it to the IntegrationID enum in integration_ids.py
## Then, add a new entry to the INTEGRATION_CONFIGS dictionary below. Aura integration is optional.
## If the chain is not yet supported, add it to the Chain enum in chains.py and add RPCs to web3_utils.py.


@dataclass
class IntegrationConfig:
    chain: Chain
    start_block: int
    incentivized_token: str
    incentivized_token_decimals: int
    pool_address: str
    gauge_address: str | None = None
    aura_address: str | None = None


INTEGRATION_CONFIGS: Dict[IntegrationID, IntegrationConfig] = {
    IntegrationID.BALANCER_V3_ETHEREUM_TESTING: IntegrationConfig(
        chain=Chain.ETHEREUM,
        start_block=21374757,
        incentivized_token=Token.USDE.value,
        incentivized_token_decimals=18,
        pool_address="0xc4Ce391d82D164c166dF9c8336DDF84206b2F812",
        gauge_address="0x4B891340b51889f438a03DC0e8aAAFB0Bc89e7A6",
    ),
}


def get_integration_config(
    integration_id: IntegrationID,
) -> Optional[IntegrationConfig]:
    return INTEGRATION_CONFIGS.get(integration_id)
