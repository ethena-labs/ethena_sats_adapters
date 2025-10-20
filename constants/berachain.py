from dataclasses import dataclass
from typing import Dict

from integrations.integration_ids import IntegrationID

ZERO_ADRESS = "0x0000000000000000000000000000000000000000"

@dataclass
class BerachainPoolConfig:
    start_block: int
    pool: str
    reward_vault: str | None


BERACHAIN_CONFIGS: Dict[IntegrationID, BerachainPoolConfig] = {
    IntegrationID.BERACHAIN_LP_sUSDe_USDe_HONEY_POOL: BerachainPoolConfig(
        start_block=11814240,
        pool="0x1e1ff653525875bf0f4d41d897fe46f0fa3c2dc7",
        reward_vault="0x51d4dc2fe8ad332dc47a36480c20f9bb0d293f76"
    ),
}
