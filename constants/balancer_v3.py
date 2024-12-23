from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

from constants.chains import Chain
from integrations.integration_ids import IntegrationID

## If you want to integrate another Balancer Pool, first add it to the IntegrationID enum in integration_ids.py
## Then, add a new entry to the INTEGRATION_CONFIGS dictionary below. Aura integration is optional.
## If the chain is not yet supported, add it to the Chain enum in chains.py and add RPCs to web3_utils.py.


class Token(Enum):
    WA_ETH_USDE = (
        "0x5f9d59db355b4a60501544637b00e94082ca575b"  # Wrapped Aave Ethereum USDe
    )


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
    IntegrationID.BALANCER_V3_ETHEREUM_USDE_USDT: IntegrationConfig(
        chain=Chain.ETHEREUM,
        start_block=21467086,
        incentivized_token=Token.WA_ETH_USDE.value,
        incentivized_token_decimals=18,
        pool_address="0xc1D48bB722a22Cc6Abf19faCbE27470F08B3dB8c",
        gauge_address="0x95d260ac86B58D458187C819f87aAd2c7c4203eF",
    ),
}


def get_integration_config(
    integration_id: IntegrationID,
) -> Optional[IntegrationConfig]:
    return INTEGRATION_CONFIGS.get(integration_id)
