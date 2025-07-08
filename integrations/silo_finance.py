import logging
from rich.console import Console

from constants.silo_finance import SILO_FINANCE_INTEGRATION_ID_TO_START_BLOCK
from constants.summary_columns import SummaryColumn
from integrations.integration_ids import IntegrationID as IntID
from constants.chains import Chain
from utils.silo_finance import SiloFinance

logger = logging.getLogger("Silo Finance LP-eUSDe")
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    console = Console()

    integration = SiloFinance(
        integration_id=IntID.SILO_FINANCE_LP_USDE,
        start_block=SILO_FINANCE_INTEGRATION_ID_TO_START_BLOCK[
            IntID.SILO_FINANCE_LP_USDE
        ],
        chain=Chain.ETHEREUM,
        summary_cols=[SummaryColumn.SILO_FINANCE_LP_USDE_PTS],
        reward_multiplier=30,
        balance_multiplier=1,
    )

    # Without cached data
    # without_cached_data_output = integration.get_block_balances(
    #     cached_data={}, blocks=[22693183, 22695554 + 1]
    # )

    # console.print("=" * 120)
    # console.print("Run without cached data", without_cached_data_output)
    # console.print("=" * 120, "\n" * 5)

    # With cached data, using the previous output so there is no need
    # to fetch the previous blocks again
    with_cached_data_output = integration.get_block_balances(
        # cached_data=without_cached_data_output,
        cached_data={},
        blocks=[22814115],  # First block with transfer event
    )
    console.print("Run with cached data", with_cached_data_output)
    breakpoint()
    # console.print("=" * 120)
