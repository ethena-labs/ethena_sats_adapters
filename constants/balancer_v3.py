from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

from constants.chains import Chain
from constants.balancer import Token
from integrations.integration_ids import IntegrationID

## If you want to integrate another Balancer Pool, first add it to the IntegrationID enum in integration_ids.py
## Then, add a new entry to the INTEGRATION_CONFIGS dictionary below. Aura integration is optional.
## If the chain is not yet supported, add it to the Chain enum in chains.py and add RPCs to web3_utils.py.


class WrappedToken(Enum):  # Ensure address is checksummed
    WA_ETH_USDE = (
        "0x5F9D59db355b4A60501544637b00e94082cA575b"  # Wrapped Aave Ethereum USDe
    )
    WA_PLA_USDE = (
        "0xC63F1a8c0cD4493E18f6f3371182BE01Ce0BeF02"  # Wrapped Aave Plasma USDe
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
        incentivized_token=WrappedToken.WA_ETH_USDE.value,
        incentivized_token_decimals=18,
        pool_address="0xc1D48bB722a22Cc6Abf19faCbE27470F08B3dB8c",
        gauge_address="0x95d260ac86B58D458187C819f87aAd2c7c4203eF",
    ),
    IntegrationID.BALANCER_V3_PLASMA_USDE_USDT: IntegrationConfig(
        chain=Chain.PLASMA,
        start_block=1727318,
        incentivized_token=WrappedToken.WA_PLA_USDE.value,
        incentivized_token_decimals=18,
        pool_address="0x6a74BE33B5393D8A3EbA4D69B78f9D9da947C48c",
        gauge_address=None,
    ),
    IntegrationID.BALANCER_V3_PLASMA_SUSDE_USDT: IntegrationConfig(
        chain=Chain.PLASMA,
        start_block=1726616,
        incentivized_token=Token.SUSDE.value,
        incentivized_token_decimals=18,
        pool_address="0xd9c4e277c93374a9f8C877a9D06707a88092E8F0",
        gauge_address=None,
    ),
}


def get_integration_config(
    integration_id: IntegrationID,
) -> Optional[IntegrationConfig]:
    return INTEGRATION_CONFIGS.get(integration_id)
