from rich.console import Console

from constants.silo_finance import SILO_FINANCE_INTEGRATION_ID_TO_START_BLOCK
from constants.summary_columns import SummaryColumn
from integrations.integration_ids import IntegrationID as IntID
from constants.chains import Chain
from utils.silo_finance import SiloFinance

if __name__ == "__main__":
    console = Console()
    integration_id = IntID.SILO_FINANCE_LP_SUSDE_JUL_31_EXPIRY
    integration = SiloFinance(
        integration_id=integration_id,
        start_block=SILO_FINANCE_INTEGRATION_ID_TO_START_BLOCK[integration_id],
        chain=Chain.ETHEREUM,
        summary_cols=[SummaryColumn.SILO_FINANCE_LP_SUSDE_JUL_31_PTS],
        reward_multiplier=30,
        balance_multiplier=1,
    )

    # Without cached data
    without_cached_data_output = integration.get_block_balances(
        cached_data={}, blocks=[22726532]
    )
    console.print("Run without cached data", without_cached_data_output)
    # Check that the output is correct~ish
    assert without_cached_data_output[22726532] == {
        "0x791D1ec51D931186c1d4B80E753B7155DD98f741": 5.0
    }

    # Use cache data to get the next blocks
    with_cached_data_output = integration.get_block_balances(
        cached_data=without_cached_data_output,
        blocks=[22767688],
    )
    console.print("Run with cached data", with_cached_data_output)
    assert with_cached_data_output[22767688] == {
        "0x791D1ec51D931186c1d4B80E753B7155DD98f741": 0.0,
        "0x62a4A8f9f5F3AaE9Ee9CEE780285A0D501C12d09": 17.71744,
        "0x7FDe637d685A5486CCb1B0a8eF658Ad1a08e8337": 234388.684906,
    }
