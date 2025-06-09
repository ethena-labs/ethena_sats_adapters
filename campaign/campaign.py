from typing import List

from integrations.beefy_cached_balance_example_integration import (
    BeefyCachedBalanceIntegration,
)
from integrations.claimed_ena_example_integration import ClaimedEnaIntegration
from integrations.kamino_l2_delegation_example_integration import (
    KaminoL2DelegationExampleIntegration,
)
from integrations.ratex_l2_delegation_example_integration import (
    RatexL2DelegationExampleIntegration,
)

from constants.chains import Chain
from constants.pendle import PENDLE_USDE_JULY_DEPLOYMENT_BLOCK
from constants.summary_columns import SummaryColumn
from web3 import Web3
from constants.evaa import EVAA_USDE_START_BLOCK, EVAA_SUSDE_START_BLOCK
from integrations.stonfi_integration import StonFiIntegration
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from integrations.pendle_lpt_integration import PendleLPTIntegration
from integrations.pendle_yt_integration import PendleYTIntegration
from integrations.evaa_integration import EvaaIntegration
from integrations.template import ProtocolNameIntegration
from utils import pendle

from constants.example_integrations import (
    ACTIVE_ENA_START_BLOCK_EXAMPLE,
    BEEFY_ARBITRUM_START_BLOCK_EXAMPLE,
    KAMINO_SUSDE_COLLATERAL_START_BLOCK_EXAMPLE,
    RATEX_EXAMPLE_USDE_START_BLOCK,
)
from constants.stonfi import STONFI_USDE_START_BLOCK
from constants.chains import Chain
from constants.pendle import PENDLE_USDE_JULY_DEPLOYMENT_BLOCK
from constants.summary_columns import SummaryColumn

# TODO: Add your integration here
INTEGRATIONS: List[Integration] = [
    # STON.fi L2 Delegation TON chain, based on API calls
    StonFiIntegration(
        integration_id=IntegrationID.STONFI_USDE,
        start_block=STONFI_USDE_START_BLOCK,
        summary_cols=[
            SummaryColumn.STONFI_USDE_PTS,
        ],
        chain=Chain.TON,
        reward_multiplier=30,
    ),
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
    EvaaIntegration(
        integration_id=IntegrationID.EVAA_TON_USDE,
        start_block=EVAA_USDE_START_BLOCK,
        summary_cols=[SummaryColumn.EVAA_USDE_PTS],
        chain=Chain.TON,
        reward_multiplier=20,
    ),
    EvaaIntegration(
        integration_id=IntegrationID.EVAA_TON_SUSDE,
        start_block=EVAA_SUSDE_START_BLOCK,
        summary_cols=[SummaryColumn.EVAA_SUSDE_PTS],
        chain=Chain.TON,
        reward_multiplier=5,
    ),
    # Example integration using cached user balances for improved performance,
    # reads from previous balance snapshots
    ClaimedEnaIntegration(
        integration_id=IntegrationID.CLAIMED_ENA_EXAMPLE,
        start_block=ACTIVE_ENA_START_BLOCK_EXAMPLE,
        summary_cols=[SummaryColumn.CLAIMED_ENA_PTS_EXAMPLE],
        reward_multiplier=1,
    ),
    # Cached balances integration example, based on API calls
    BeefyCachedBalanceIntegration(
        integration_id=IntegrationID.BEEFY_CACHED_BALANCE_EXAMPLE,
        start_block=BEEFY_ARBITRUM_START_BLOCK_EXAMPLE,
        summary_cols=[SummaryColumn.BEEFY_CACHED_BALANCE_EXAMPLE],
        chain=Chain.ARBITRUM,
        reward_multiplier=1,
    ),
    # L2 Delegation example for non EVM chains, based on ts script
    KaminoL2DelegationExampleIntegration(
        integration_id=IntegrationID.KAMINO_SUSDE_COLLATERAL_EXAMPLE,
        start_block=KAMINO_SUSDE_COLLATERAL_START_BLOCK_EXAMPLE,
        market_address="BJnbcRHqvppTyGesLzWASGKnmnF1wq9jZu6ExrjT7wvF",
        token_address="EwBTjwCXJ3TsKP8dNTYnzRmBWRd6h48FdLFSAGJ3sCtx",
        decimals=9,
        chain=Chain.SOLANA,
        reward_multiplier=1,
    ),
    # L2 Delegation example for non EVM chains, based on API calls
    RatexL2DelegationExampleIntegration(
        integration_id=IntegrationID.RATEX_USDE_EXAMPLE,
        start_block=RATEX_EXAMPLE_USDE_START_BLOCK,
        summary_cols=[
            SummaryColumn.RATEX_EXAMPLE_PTS,
        ],
        chain=Chain.SOLANA,
        reward_multiplier=1,
    ),
    # Simple Integration class examples (outdated),
    # don't use these anymore
    PendleLPTIntegration(
        integration_id=IntegrationID.PENDLE_USDE_LPT,
        start_block=PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        sy_contract=pendle.sy_contract,
        lp_contract=pendle.lpt_contract,
        summary_cols=[SummaryColumn.PENDLE_SHARDS],
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
    ),
    PendleLPTIntegration(
        integration_id=IntegrationID.PENDLE_ARBITRUM_USDE_LPT,
        start_block=PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        sy_contract=pendle.usde_arb_SY_contract,
        lp_contract=pendle.usde_arb_LPT_contract,
        summary_cols=[SummaryColumn.PENDLE_ARBITRUM_SHARDS],
        chain=Chain.ARBITRUM,
        reward_multiplier=20,
    ),
    PendleYTIntegration(
        integration_id=IntegrationID.PENDLE_USDE_YT,
        start_block=PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        summary_cols=[SummaryColumn.PENDLE_SHARDS],
        yt_contract=pendle.yt_contract,
        chain=Chain.ETHEREUM,
        reward_multiplier=20,
    ),
    PendleYTIntegration(
        integration_id=IntegrationID.PENDLE_ARBITRUM_USDE_YT,
        start_block=PENDLE_USDE_JULY_DEPLOYMENT_BLOCK,
        summary_cols=[SummaryColumn.PENDLE_ARBITRUM_SHARDS],
        yt_contract=pendle.usde_arb_YT_contract,
        chain=Chain.ARBITRUM,
        reward_multiplier=20,
    ),
]


def get_integrations() -> List[Integration]:
    return INTEGRATIONS
