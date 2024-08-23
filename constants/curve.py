from constants.summary_columns import SummaryColumn
from dataclasses import dataclass
from constants.chains import Chain
from constants.integration_ids import IntegrationID


@dataclass
class RewardContractConfig:
    abi_filename: str
    address: str
    chain: Chain
    genesis_block: int
    reward_multiplier: int
    balance_multiplier: int
    integration_id: IntegrationID
    state_arg_no: int
    event_arg_name: str


CURVE_LLAMALEND = [
    RewardContractConfig(
        abi_filename="abi/curve_llamalend_controller.json",
        address="0x74f88Baa966407b50c10B393bBD789639EFfE78B",
        chain=Chain.ETHEREUM,
        genesis_block=20148558,
        reward_multiplier=20,
        balance_multiplier=1,
        integration_id=IntegrationID.CURVE_ETHEREUM_USDE_BORROWERS,
        state_arg_no=0,
        event_arg_name="user",
    ),
    RewardContractConfig(
        abi_filename="abi/curve_llamalend_controller.json",
        address="0xB536FEa3a01c95Dd09932440eC802A75410139D6",
        chain=Chain.ETHEREUM,
        genesis_block=19999153,
        reward_multiplier=5,
        balance_multiplier=1,
        integration_id=IntegrationID.CURVE_ETHEREUM_SUSDE_BORROWERS,
        state_arg_no=0,
        event_arg_name="user",
    ),
]

SUMMARY_COLS = {
    "llamalend": SummaryColumn.CURVE_LLAMALEND_SHARDS,
}
