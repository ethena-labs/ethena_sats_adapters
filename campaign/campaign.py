from typing import List
from web3 import Web3

from constants.chains import Chain
from constants.pendle import PENDLE_USDE_JULY_DEPLOYMENT_BLOCK
from constants.summary_columns import SummaryColumn
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from integrations.pendle_lpt_integration import PendleLPTIntegration
from integrations.pendle_yt_integration import PendleYTIntegration
from integrations.template import ProtocolNameIntegration

# TODO: Add your integration here
INTEGRATIONS: List[Integration] = [
    # Template integration
    ProtocolNameIntegration(
        integration_id=IntegrationID.EXAMPLE,
        start_block=20000000,
        summary_cols=[SummaryColumn.TEMPLATE_PTS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
        excluded_addresses={
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
        },
        end_block=40000000,
    ),
    # Examples
    PendleLPTIntegration(
        integration_id=IntegrationID.PENDLE_USDE_LPT,
        start_block=PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        sy_contract=None,
        lp_contract=None,
        summary_cols=[SummaryColumn.PENDLE_SHARDS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
    ),
    PendleLPTIntegration(
        integration_id=IntegrationID.PENDLE_ARBITRUM_USDE_LPT,
        start_block=PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        sy_contract=None,
        lp_contract=None,
        summary_cols=[SummaryColumn.PENDLE_ARBITRUM_SHARDS],
        chain=Chain.ARBITRUM,
        reward_multiplier=20,
    ),
    PendleYTIntegration(
        integration_id=IntegrationID.PENDLE_USDE_YT,
        start_block=PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        summary_cols=[SummaryColumn.PENDLE_SHARDS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
    ),
    PendleYTIntegration(
        integration_id=IntegrationID.PENDLE_ARBITRUM_USDE_YT,
        start_block=PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        summary_cols=[SummaryColumn.PENDLE_ARBITRUM_SHARDS],
        chain=Chain.ARBITRUM,
        reward_multiplier=20,
    ),
]


def get_integrations() -> List[Integration]:
    return INTEGRATIONS
