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
