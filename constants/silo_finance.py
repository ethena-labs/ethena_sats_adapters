from dataclasses import dataclass

from integrations.integration_ids import IntegrationID as IntID


@dataclass
class SiloFinanceMarket:
    address: str
    start_block: int
    non_borrowable_token_address: str


PAGINATION_SIZE = 1000


SILO_FINANCE_MARKETS = [
    # https://etherscan.io/address/0xB0291953571aF3D51EdfE9DAA94beDfa7C8aaf94
    SiloFinanceMarket(
        address="0xB0291953571aF3D51EdfE9DAA94beDfa7C8aaf94",
        start_block=22693183,
        non_borrowable_token_address="0x98732e72D33279488FebCCa58628C83574699160",
    ),
    # https://etherscan.io/address/0x46d30718F0372713b989F91f9f0Be1Bf5Cf5F082
    # SiloFinanceMarket(
    #     address="0x46d30718F0372713b989F91f9f0Be1Bf5Cf5F082",
    #     start_block=22694943,
    #     non_borrowable_token_address="0x7a3E2284DB8F2b9d6Bcc54faB182284FaC53f51b",
    # ),
    # https://etherscan.io/address/0x4902F25cf6486840F9dED17A6b3AF74fE107fffc
    # SiloFinanceMarket(
    #     address="0x4902F25cf6486840F9dED17A6b3AF74fE107fffc",
    #     start_block=22695554,
    #     non_borrowable_token_address="0x0000000000000000000000000000000000000000",
    # ),
]

SILO_FINANCE_INTEGRATION_ID_TO_MARKET = {
    IntID.SILO_FINANCE_LP_USDE: SILO_FINANCE_MARKETS[0],
}

# NOTE: the first deployment block is the earliest block where any of the markets are deployed
SILO_FINANCE_INTEGRATION_ID_TO_START_BLOCK = {
    IntID.SILO_FINANCE_LP_USDE: SILO_FINANCE_MARKETS[0].start_block,
}
