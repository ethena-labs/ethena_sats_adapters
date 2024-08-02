from constants.gmx import GMX_WSTETH_USDE_MARKET_BLOCK, WSTETH_TOKEN_ADDRESS, GMX_WSTETH_USDE_MARKET_ADDRESS, USDE_TOKEN_ADDRESS, WETH_TOKEN_ADDRESS

from constants.integration_ids import IntegrationID
from utils.gmx import GMXLPIntegration

if __name__ == "__main__":
    gmx_integration = GMXLPIntegration(
        IntegrationID.GMX_WSTETH_USDE_LP,
        GMX_WSTETH_USDE_MARKET_BLOCK,
        GMX_WSTETH_USDE_MARKET_ADDRESS,
        WETH_TOKEN_ADDRESS,
        WSTETH_TOKEN_ADDRESS,
        USDE_TOKEN_ADDRESS,
    )
    print(gmx_integration.get_participants())
    print(
        gmx_integration.get_balance(
            "0x596CDbB0d4b74Cb5dCdf86613d8012E0cD3E522f", 238329658
        )
    )
