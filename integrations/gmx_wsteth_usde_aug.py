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
            "0x8F091A33f310EFd8Ca31f7aE4362d6306cA6Ec8d", 237999816
        )
    )
