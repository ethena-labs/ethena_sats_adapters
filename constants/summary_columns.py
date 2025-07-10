from enum import Enum


class SummaryColumnType(Enum):
    ETHENA_PTS = "ethena_pts"
    ETHEREAL_PTS = "ethereal_pts"


class SummaryColumn(Enum):
    TEMPLATE_PTS = ("template_pts", SummaryColumnType.ETHENA_PTS)
    PENDLE_SHARDS = ("pendle_shards", SummaryColumnType.ETHENA_PTS)
    PENDLE_ARBITRUM_SHARDS = ("pendle_arbtrium_shards", SummaryColumnType.ETHENA_PTS)
    PENDLE_MANTLE_SHARDS = ("pendle_mantle_shards", SummaryColumnType.ETHENA_PTS)
    SYNTHETIX_ARBITRUM_SHARDS = (
        "synthetix_arbitrum_shards",
        SummaryColumnType.ETHENA_PTS,
    )

    AMBIENT_SCROLL_SHARDS = ("ambient_scroll_shards", SummaryColumnType.ETHENA_PTS)
    AMBIENT_SWELL_SHARDS = ("ambient_swell_shards", SummaryColumnType.ETHENA_PTS)

    THALA_SHARDS = ("thala_shards", SummaryColumnType.ETHENA_PTS)

    ECHELON_SHARDS = ("echelon_shards", SummaryColumnType.ETHENA_PTS)

    NURI_SHARDS = ("nuri_shards", SummaryColumnType.ETHENA_PTS)
    LENDLE_MANTLE_SHARDS = ("lendle_mantle_shards", SummaryColumnType.ETHENA_PTS)

    RHO_MARKETS_SCROLL_SHARDS = (
        "rho_markets_scroll_shards",
        SummaryColumnType.ETHENA_PTS,
    )

    RAMSES_SHARDS = ("ramses_shards", SummaryColumnType.ETHENA_PTS)

    GMX_ARBITRUM_SHARDS = ("gmx_arbitrum_shards", SummaryColumnType.ETHENA_PTS)

    CURVE_LLAMALEND_SHARDS = ("curve_llamalend_shards", SummaryColumnType.ETHENA_PTS)

    CORK_PSM_PTS = ("cork_psm_shards", SummaryColumnType.ETHENA_PTS)

    CLAIMED_ENA_PTS_EXAMPLE = ("claimed_ena_example", SummaryColumnType.ETHENA_PTS)

    BEEFY_CACHED_BALANCE_EXAMPLE = (
        "beefy_cached_balance_example",
        SummaryColumnType.ETHENA_PTS,
    )

    TEMPEST_SWELL_SHARDS = ("tempest_swell_shards", SummaryColumnType.ETHENA_PTS)

    KAMINO_DELEGATED_PTS_EXAMPLE = (
        "kamino_delegated_pts_example",
        SummaryColumnType.ETHENA_PTS,
    )

    RATEX_EXAMPLE_PTS = ("ratex_example_pts", SummaryColumnType.ETHENA_PTS)

    FIVA_EXAMPLE_PTS = ("fiva_example_pts", SummaryColumnType.ETHENA_PTS)

    STONFI_USDE_PTS = ("stonfi_usde_pts", SummaryColumnType.ETHENA_PTS)

    VENUS_SUSDE_PTS = ("venus_susde_pts", SummaryColumnType.ETHENA_PTS)

    # EVAA Protocol
    EVAA_USDE_PTS = ("evaa_usde_pts", SummaryColumnType.ETHENA_PTS)
    EVAA_SUSDE_PTS = ("evaa_susde_pts", SummaryColumnType.ETHENA_PTS)

    # Sentiment
    SENTIMENT_USDE_PTS = ("sentiment_usde_pts", SummaryColumnType.ETHENA_PTS)

    MORPHO_SUSDE_SUSDS_PTS = ("morpho_susde_susds_pts", SummaryColumnType.ETHENA_PTS)

    # TermMax
    TERMMAX_SUSDE_PTS = ("termmax_susde_pts", SummaryColumnType.ETHENA_PTS)
    TERMMAX_PT_SUSDE_25SEP2025_PTS = ("termmax_pt_susde_25sep2025_pts", SummaryColumnType.ETHENA_PTS)

    def __init__(self, column_name: str, col_type: SummaryColumnType):
        self.column_name = column_name
        self.col_type = col_type

    def get_col_name(self) -> str:
        return self.column_name

    def get_col_type(self) -> SummaryColumnType:
        return self.col_type
