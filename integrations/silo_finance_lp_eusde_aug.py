from rich.console import Console

from constants.silo_finance import SILO_FINANCE_INTEGRATION_ID_TO_START_BLOCK
from constants.summary_columns import SummaryColumn
from integrations.integration_ids import IntegrationID as IntID
from constants.chains import Chain
from utils.silo_finance import SiloFinance

if __name__ == "__main__":
    console = Console()
    integration_id = IntID.SILO_FINANCE_LP_EUSDE_AUG_14_EXPIRY
    integration = SiloFinance(
        integration_id=integration_id,
        start_block=SILO_FINANCE_INTEGRATION_ID_TO_START_BLOCK[integration_id],
        chain=Chain.ETHEREUM,
        summary_cols=[SummaryColumn.SILO_FINANCE_LP_EUSDE_AUG_14_PTS],
        reward_multiplier=30,
        balance_multiplier=1,
    )

    # Without cached data
    without_cached_data_output = integration.get_block_balances(
        cached_data={}, blocks=[22726278]
    )
    console.print("Run without cached data", without_cached_data_output)
    # Check that the output is correct~ish
    assert without_cached_data_output[22726278] == {
        "0xdEDcF5806c4968C6397eeE97e68047bdA339d0c1": 4.0
    }

    # Use cache data to get the next blocks
    with_cached_data_output = integration.get_block_balances(
        cached_data=without_cached_data_output,
        blocks=[22740147],
    )
    console.print("Run with cached data", with_cached_data_output)
    assert with_cached_data_output[22740147] == {
        "0xdEDcF5806c4968C6397eeE97e68047bdA339d0c1": 5.0,
        "0x62a4A8f9f5F3AaE9Ee9CEE780285A0D501C12d09": 25.447709,
    }
