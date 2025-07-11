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
        integration_id=IntID.SILO_FINANCE_LP_SUSDE_SEP_25_EXPIRY,
        start_block=SILO_FINANCE_INTEGRATION_ID_TO_START_BLOCK[
            IntID.SILO_FINANCE_LP_SUSDE_SEP_25_EXPIRY
        ],
        chain=Chain.ETHEREUM,
        summary_cols=[SummaryColumn.SILO_FINANCE_LP_SUSDE_SEP_25_EXPIRY_PTS],
        reward_multiplier=30,
        balance_multiplier=1,
    )

    # Without cached data
    without_cached_data_output = integration.get_block_balances(
        cached_data={}, blocks=[22693183, 22755000]
    )
    console.print("Run without cached data", without_cached_data_output)
    # Check that the output is correct~ish
    assert without_cached_data_output[22755000] == {
        "0x62a4A8f9f5F3AaE9Ee9CEE780285A0D501C12d09": 18.194513,
        "0xeb80e76443c1bFa85dF46075f52a43ae1572003a": 30578.64522,
    }

    # Use cache data to get the next blocks
    with_cached_data_output = integration.get_block_balances(
        cached_data=without_cached_data_output,
        blocks=[22814115],
    )
    console.print("Run with cached data", with_cached_data_output)
    assert with_cached_data_output[22814115] == {
        "0x62a4A8f9f5F3AaE9Ee9CEE780285A0D501C12d09": 18.194513,
        "0xeb80e76443c1bFa85dF46075f52a43ae1572003a": 30578.64522,
        "0x432FD970d8867b56e7197290BCd03C92A325AB7b": 620.451445,
        "0xdD84Ce1aDcb3A4908Db61A1dFA3353C3974c5a2B": 145426.301041,
        "0x8467241838Bc761D9Ef4F8ae6790Ede292fbA2F9": 1e-6,
        "0x23ce39C9AB29D00fCa9B83a50F64A67837c757C5": 4759.421793,
    }
