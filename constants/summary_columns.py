from enum import Enum


class SummaryColumnType(Enum):
    SHARDS = "shards"
    BALANCE = "balance"


class SummaryColumn(Enum):
    PENDLE_SHARDS = ("pendle_shards", SummaryColumnType.SHARDS)
    PENDLE_ARBTRIUM_SHARDS = ("pendle_arbtrium_shards", SummaryColumnType.SHARDS)
    PENDLE_MANTLE_SHARDS = ("pendle_mantle_shards", SummaryColumnType.SHARDS)
    MEZO_SATS = ("mezo_sats", SummaryColumnType.SHARDS)

    USDE_ARB_SATS = ("usde_arb_sats", SummaryColumnType.SHARDS)
    USDE_BLAST_SATS = ("usde_blast_sats", SummaryColumnType.SHARDS)
    USDE_MANTLE_SATS = ("usde_mantle_sats", SummaryColumnType.SHARDS)

    INFINEX_MAINNET_SATS = ("infinex_mainnet_sats", SummaryColumnType.SHARDS)
    INFINEX_ARBITRUM_SATS = ("infinex_arbitrum_sats", SummaryColumnType.SHARDS)

    SYMBIOTIC_SATS = ("symbiotic_sats", SummaryColumnType.SHARDS)
    MELLOW_SATS = ("mellow_sats", SummaryColumnType.SHARDS)
    GEARBOX_SATS = ("gearbox_shards", SummaryColumnType.SHARDS)
    GEARBOX_ARBITRUM_SATS = ("gearbox_arbitrum_sats", SummaryColumnType.SHARDS)

    ACTIVE_ENA = ("active_ena", SummaryColumnType.BALANCE)

    SYNTHETIX_ARBITRUM_SHARDS = ("synthetix_arbitrum_shards", SummaryColumnType.SHARDS)

    def __init__(self, column_name: str, col_type: SummaryColumnType):
        self.column_name = column_name
        self.col_type = col_type

    def get_col_name(self) -> str:
        return self.column_name

    def get_col_type(self) -> str:
        return self.col_type
