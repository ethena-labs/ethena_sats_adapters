from constants.chains import Chain
from integrations.integration_ids import IntegrationID
from utils.kodiak import KodiakIntegration

if __name__ == "__main__":
    integration = KodiakIntegration(
        IntegrationID.KODIAK_USDE,
        1,
        Chain.BERACHAIN
    )

    print(integration.get_block_balances({
        1: {
            "0x0000000000000000000000000000000000000000": 100.0
        }
    }, [12886286, 1]))
