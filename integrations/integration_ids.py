from enum import Enum

from constants.integration_token import Token


class IntegrationID(Enum):
    EXAMPLE = ("example", "Example", Token.USDE)
    PENDLE_USDE_LPT = ("pendle_effective_lpt_held", "Pendle USDe LPT")
    PENDLE_USDE_YT = ("pendle_yt_held", "Pendle USDe YT")
    PENDLE_SUSDE_LPT_APRIL_EXPIRY = (
        "pendle_effective_susde_apr_lpt_held",
        "Pendle sUSDe LPT (April expiry)",
        Token.SUSDE,
    )
    PENDLE_SUSDE_YT_APRIL_EXPIRY = (
        "pendle_susde_apr_yt_held",
        "Pendle sUSDe YT (April expiry)",
        Token.SUSDE,
    )
    PENDLE_SUSDE_LPT_JULY_EXPIRY = (
        "pendle_effective_susde_jul_lpt_held",
        "Pendle sUSDe LPT (July expiry)",
        Token.SUSDE,
    )
    PENDLE_SUSDE_YT_JULY_EXPIRY = (
        "pendle_susde_jul_yt_held",
        "Pendle sUSDe YT (July expiry)",
        Token.SUSDE,
    )
    PENDLE_SUSDE_LPT_SEPT_EXPIRY = (
        "pendle_effective_susde_sep_lpt_held",
        "Pendle sUSDe LPT (Sept expiry)",
        Token.SUSDE,
    )
    PENDLE_SUSDE_YT_SEPT_EXPIRY = (
        "pendle_susde_sep_yt_held",
        "Pendle sUSDe YT (Sept expiry)",
        Token.SUSDE,
    )
    PENDLE_ENA_LPT = ("pendle_effective_ena_lpt_held", "Pendle ENA LPT", Token.ENA)
    PENDLE_ENA_YT = ("pendle_ena_yt_held", "Pendle ENA YT", Token.ENA)
    PENDLE_ARBITRUM_USDE_LPT = (
        "pendle_arbtrium_effective_lpt_bal",
        "Pendle Arbitrum USDe LPT",
    )
    PENDLE_ARBITRUM_USDE_YT = ("pendle_arbtrium_yt_bal", "Pendle Arbitrum USDe YT")
    PENDLE_KARAK_USDE_LPT = ("pendle_karak_usde_lpt_held", "Pendle Karak USDe LPT")
    PENDLE_KARAK_USDE_YT = ("pendle_karak_usde_yt_held", "Pendle Karak USDe YT")
    PENDLE_KARAK_SUSDE_LPT = (
        "pendle_karak_susde_lpt_held",
        "Pendle Karak sUSDe LPT",
        Token.SUSDE,
    )
    PENDLE_KARAK_SUSDE_YT = (
        "pendle_karak_susde_yt_held",
        "Pendle Karak sUSDe YT",
        Token.SUSDE,
    )
    PENDLE_MANTLE_USDE_LPT = (
        "pendle_mantle_effective_lpt_bal",
        "Pendle Mantle USDe LPT",
    )
    PENDLE_MANTLE_USDE_YT = ("pendle_mantle_yt_bal", "Pendle Mantle USDe YT")
    PENDLE_ZIRCUIT_USDE_LPT = (
        "pendle_effective_zircuit_usde_lpt_held",
        "Pendle Zircuit USDe LPT",
    )
    PENDLE_ZIRCUIT_USDE_YT = ("pendle_zircuit_usde_yt_held", "Pendle Zircuit USDe YT")

    # Thala
    THALA_SUSDE_LP = (
        "thala_susde_usdc_lp",
        "Thala sUSDe/USDC LP",
        Token.SUSDE,
    )
    
    # Echelon
    ECHELON_SUSDE_COLLATERAL = (
        "echelon_susde_collateral",
        "Echelon sUSDe Collateral",
        Token.SUSDE,
    )

    # Termmax
    TERMMAX_USDE = (
        "termmax_usde",
        "Termmax USDe",
        Token.USDE,
    )
    TERMMAX_SUSDE = (
        "termmax_susde",
        "Termmax sUSDe",
        Token.SUSDE,
    )

    # Stake DAO
    STAKEDAO_SUSDE_JULY_LPT = (
        "stakedao_susde_july_effective_lpt_held",
        "Stake DAO sUSDe July LPT",
        Token.SUSDE,
    )
    STAKEDAO_SUSDE_SEPT_LPT = (
        "stakedao_susde_sept_effective_lpt_held",
        "Stake DAO sUSDe Sept LPT",
        Token.SUSDE,
    )
    STAKEDAO_USDE_JULY_LPT = (
        "stakedao_usde_july_effective_lpt_held",
        "Stake DAO USDe July LPT",
        Token.USDE,
    )

    # PENPIE
    PENPIE_SUSDE_JULY_LPT = (
        "penpie_susde_july_effective_lpt_held",
        "PENPIE sUSDe July LPT",
        Token.SUSDE,
    )
    PENPIE_Karak_sUSDe_26SEP2024_LPT = (
        "PENPIE_Karak_sUSDe_26SEP2024_effective_lpt_held",
        "Karak_sUSDe_26SEP2024",
        Token.SUSDE,
    )
    PENPIE_Karak_USDE_26SEP2024_LPT = (
        "PENPIE_Karak_USDE_26SEP2024_effective_lpt_held",
        "Karak_USDE_26SEP2024",
        Token.USDE,
    )
    PENPIE_sUSDe25APR2024_LPT = (
        "PENPIE_sUSDe25APR2024_effective_lpt_held",
        "sUSDe25APR2024",
        Token.SUSDE,
    )
    PENPIE_sUSDe26SEP2024_LPT = (
        "PENPIE_sUSDe26SEP2024_effective_lpt_held",
        "sUSDe26SEP2024",
        Token.SUSDE,
    )
    PENPIE_USDe25JUL2024_LPT = (
        "PENPIE_USDe25JUL2024_effective_lpt_held",
        "USDe25JUL2024",
        Token.USDE,
    )
    PENPIE_Zircuit_USDe27JUN2024_LPT = (
        "PENPIE_Zircuit_USDe27JUN2024_effective_lpt_held",
        "Zircuit_USDe27JUN2024",
        Token.USDE,
    )
    PENPIE_ENA29AUG2024_LPT = (
        "PENPIE_ENA29AUG2024_effective_lpt_held",
        "ENA29AUG2024",
        Token.ENA,
    )
    PENPIE_USDE_ARB_AUG2024_LPT = (
        "PENPIE_USDE_ARB_AUG2024_effective_lpt_held",
        "USDE_ARB_AUG2024",
        Token.USDE,
    )
    PENPIE_USDe_24OCT2024_LPT = (
        "PENPIE_USDe_24OCT202_effective_lpt_held4",
        "USDe_24OCT2024",
        Token.USDE,
    )
    PENPIE_ENA_31OCT2024_LPT = (
        "PENPIE_ENA_31OCT2024_effective_lpt_held",
        "ENA_31OCT2024",
        Token.ENA,
    )
    PENPIE_rsUSDe_26SEP2024_LPT = (
        "PENPIE_rsUSDe_26SEP2024_effective_lpt_held",
        "rsUSDe_26SEP2024",
        Token.USDE,
    )
    PENPIE_USDe_26DEC2024_LPT = (
        "PENPIE_USDe_26DEC2024_effective_lpt_held",
        "USDe_26DEC2024",
        Token.USDE,
    )
    PENPIE_sUSDE_26DEC2024_LPT = (
        "PENPIE_sUSDE_26DEC2024_effective_lpt_held",
        "sUSDE_26DEC2024",
        Token.SUSDE,
    )
    PENPIE_sUSDE_24OCT2024_LPT = (
        "PENPIE_sUSDE_24OCT2024_effective_lpt_held",
        "sUSDE_24OCT2024",
        Token.SUSDE,
    )
    PENPIE_rsENA_26SEP2024_LPT = (
        "PENPIE_rsENA_26SEP2024_effective_lpt_held",
        "rsENA_26SEP2024",
        Token.ENA,
    )
    PENPIE_USDE_ARB_NOV2024_LPT = (
        "PENPIE_USDE_ARB_NOV2024_effective_lpt_held",
        "USDE_ARB_NOV2024",
        Token.USDE,
    )

    # EQUILIBRIA
    EQUILIBRIA_SUSDE_SEPT_LPT = (
        "equilibria_susde_sept_effective_lpt_held",
        "Equilibria sUSDe Sept LPT",
        Token.SUSDE,
    )
    EQUILIBRIA_Karak_SUSDE_SEPT_SEPT = (
        "equilibria_karak_susde_sept_effective_lpt_held",
        "Equilibria Karak sUSDe Sept LPT",
        Token.SUSDE,
    )
    EQUILIBRIA_Karak_USDE_SEPT_LPT = (
        "equilibria_karak_usde_sept_effective_lpt_held",
        "Equilibria Karak USDe Sept LPT",
        Token.USDE,
    )
    EQUILIBRIA_Zircuit_USDE_AUG_LPT = (
        "equilibria_zircuit_usde_aug_effective_lpt_held",
        "Equilibria Zircuit USDe Aug LPT",
        Token.USDE,
    )
    EQUILIBRIA_rUSDE_SEPT_LPT = (
        "equilibria_rusde_sept_effective_lpt_held",
        "Equilibria rUSDe Sept LPT",
    )
    EQUILIBRIA_USDE_LPT_EXPIRY = (
        "equilibria_usde_lpt_expiry_effective_lpt_held",
        "Equilibria USDe LPT Expiry",
        Token.USDE,
    )
    EQUILIBRIA_SUSDE_APR_EXPIRY = (
        "equilibria_susde_apr_expiry_effective_lpt_held",
        "Equilibria sUSDe Apr Expiry",
        Token.SUSDE,
    )

    # EulerV2
    EULER_USDE = ("euler_usde_deposit", "EulerV2 USDe", Token.USDE)
    EULER_SUSDE = ("euler_susde_deposit", "EulerV2 sUSDe", Token.SUSDE)

    # Term Finance
    TERM_SUSDE = ("term_susde_held", "Term Finance sUSDe", Token.SUSDE)

    # Synthetix
    SYNTHETIX_USDE_LP = (
        "synthetix_usde_arb_lp_bal",
        "Synthetix V3 Arbitrum USDe LP",
        Token.USDE,
    )

    # Lendle
    LENDLE_USDE_LPT = ("lendle_usde_lpt_bal", "Lendle Mantle USDe LPT", Token.USDE)
    LENDLE_SUSDE_LPT = ("lendle_susde_lpt_bal", "Lendle Mantle sUSDe LPT", Token.SUSDE)

    # Lyra
    LYRA_SUSDE_BULL_MAINNET = (
        "lyra_susde_bull_mainnet",
        "Lyra sUSDe Bull Vault Mainnet",
        Token.SUSDE,
    )
    LYRA_SUSDE_BULL_ARBITRUM = (
        "lyra_susde_bull_arbitrum",
        "Lyra sUSDe Bull Vault Arbitrum",
        Token.SUSDE,
    )
    LYRA_SUSDE_EXCHANGE_DEPOSIT = (
        "lyra_susde_exchange_deposit",
        "Lyra sUSDe Exchange Deposits",
        Token.SUSDE,
    )
    # Velodrome
    VELODROME_MODE_USDE = ("velodrome_mode_usde", "Velodrome Mode USDe", Token.USDE)
    VELODROME_MODE_SUSDE = ("velodrome_mode_susde", "Velodrome Mode sUSDe", Token.SUSDE)
    # Ambient
    AMBIENT_SCROLL_LP = ("ambient_usde_scroll_lp_bal", "Ambient Scroll LP", Token.USDE)
    AMBIENT_SWELL_LP = ("ambient_usde_swell_lp_bal", "Ambient Swell LP", Token.USDE)

    # Balancer V2
    BALANCER_ARBITRUM_GHO_USDE = (
        "balancer_arbitrum_gho_usde",
        "Balancer Arbitrum GHO/USDe",
        Token.USDE,
    )
    BALANCER_ARBITRUM_WAGHO_USDE = (
        "balancer_arbitrum_wagho_usde",
        "Balancer Arbitrum waGHO/USDe",
        Token.USDE,
    )
    BALANCER_ARBITRUM_GYD_SUSDE = (
        "balancer_arbitrum_gyd_susde",
        "Balancer Arbitrum GYD/sUSDe",
        Token.SUSDE,
    )
    BALANCER_ARBITRUM_SUSDE_SFRAX = (
        "balancer_arbitrum_susde_sfrax",
        "Balancer Arbitrum sUSDe/sFRAX",
        Token.SUSDE,
    )
    BALANCER_ARBITRUM_SUSDE_USDC = (
        "balancer_arbitrum_susde_usdc",
        "Balancer Arbitrum sUSDe/USDC",
        Token.SUSDE,
    )
    BALANCER_ETHEREUM_WSTETH_SUSDE = (
        "balancer_ethereum_wsteth_susde",
        "Balancer Ethereum 50wstETH/50sUSDe",
        Token.SUSDE,
    )
    BALANCER_ETHEREUM_BAOUSD_SUSDE = (
        "balancer_ethereum_baousd_susde",
        "Balancer Ethereum baoUSD/sUSDe",
        Token.SUSDE,
    )
    BALANCER_ETHEREUM_SUSDE_USDC = (
        "balancer_ethereum_susde_usdc",
        "Balancer Ethereum sUSDe/USDC",
        Token.SUSDE,
    )
    BALANCER_ETHEREUM_SUSDE_GYD = (
        "balancer_ethereum_susde_gyd",
        "Balancer Ethereum sUSDe/GYD",
        Token.SUSDE,
    )
    BALANCER_FRAXTAL_FRAX_USDE = (
        "balancer_fraxtal_frax_usde",
        "Balancer Fraxtal FRAX/USDe",
        Token.USDE,
    )
    BALANCER_FRAXTAL_SFRAX_SDAI_SUSDE = (
        "balancer_fraxtal_sfrax_sdai_susde",
        "Balancer Fraxtal sFRAX/sDAI/sUSDe",
        Token.SUSDE,
    )
    BALANCER_FRAXTAL_FRAX_USDE_DAI_USDT_USDC = (
        "balancer_fraxtal_frax_usde_dai_usdt_usdc",
        "Balancer Fraxtal FRAX/USDe/DAI/USDT/USDC",
        Token.USDE,
    )

    # Balancer V3
    BALANCER_V3_ETHEREUM_USDE_USDT = (
        "balancer_v3_ethereum_usde_usdt",
        "Balancer V3 Ethereum USDe/USDT",
        Token.USDE,
    )

    # Nuri
    NURI_USDE_LP = ("nuri_usde_lp_bal", "Nuri USDe LP", Token.USDE)

    # Merchant Moe
    MERCHANT_MOE_METH_USDE_LBT = (
        "merchant_moe_in_range_lbt_liq_held",
        "Merchant Moe mETH/USDe Liquidity Book Token",
    )
    # Rho Markets
    RHO_MARKETS_USDE_LP = (
        "rho_markets_usde_scroll_lp_bal",
        "Rho Markets Scroll USDe LP",
        Token.USDE,
    )
    # Ramses
    RAMSES_USDE_LP = ("ramses_usde_lp_bal", "Ramses USDe LP", Token.USDE)

    # Radiant
    RADIANT_USDE_CORE_ARBITRUM = (
        "radiant_usde_arb",
        "Radiant USDE Lending",
        Token.USDE,
    )

    # Splice
    SPLICE_USDE_YT = ("splice_usde_yt", "Splice USDe YT", Token.USDE)
    SPLICE_USDE_LPT = ("splice_usde_lpt", "Splice USDe LPT", Token.USDE)
    SPLICE_SUSDE_YT = ("splice_susde_yt", "Splice SUSDe YT", Token.SUSDE)
    SPLICE_SUSDE_LPT = ("splice_susde_lpt", "Splice SUSDu LPT", Token.SUSDE)

    # GMX
    GMX_USDE_POSITIONS = ("gmx_usde_positions", "GMX USDe Positions", Token.USDE)
    GMX_USDE_USDC_LP = ("gmx_usde_usdc_aug", "GMX USDe/USDc LP", Token.USDE)
    GMX_WSTETH_USDE_LP = ("gmx_wsteth_usde_aug", "GMX wstETH/USDe LP", Token.USDE)

    # CURVE
    CURVE_ETHEREUM_USDE_BORROWERS = (
        "curve_ethereum_usde_borrowers",
        "Curve.fi Ethereum USDe Borrowers",
        Token.USDE,
    )
    CURVE_ETHEREUM_SUSDE_BORROWERS = (
        "curve_ethereum_susde_borrowers",
        "Curve.fi Ethereum sUSDe Borrowers",
        Token.SUSDE,
    )

    # Beefy
    BEEFY_ARBITRUM_USDE = (
        "beefy_arbitrum_usde_held",
        "Beefy Arbitrum USDe",
        Token.USDE,
    )
    BEEFY_FRAXTAL_USDE = ("beefy_fraxtal_usde_held", "Beefy Fraxtal USDe", Token.USDE)
    BEEFY_MANTLE_USDE = ("beefy_mantle_usde_held", "Beefy Mantle USDe", Token.USDE)
    BEEFY_OPTIMISM_USDE = (
        "beefy_optimism_usde_held",
        "Beefy Optimism USDe",
        Token.USDE,
    )

    # Allstake
    ALLSTAKE_USDE = ("allstake_usde", "Allstake USDe", Token.USDE)
    ALLSTAKE_SUSDE = ("allstake_susde", "Allstake sUSDe", Token.SUSDE)

    # Inverse Finance FiRM
    FIRM_SUSDE = ("firm_susde", "Inverse Finance FiRM sUSDe", Token.SUSDE)

    # Hyperdrive
    HYPERDRIVE_SUSDE = (
        "hyperdrive_susde",
        "ElementDAO 182 Day sUSDe Hyperdrive",
        Token.SUSDE,
    )

    # Fluid
    FLUID_SUSDE = ("Fluid_susde", "Fluid sUSDe", Token.SUSDE)
    FLUID_USDE = ("Fluid_usde", "Fluid USDe", Token.USDE)
    FLUID_SUSDE_SMART = ("Fluid_susde_smart", "Fluid sUSDe Smart", Token.SUSDE)
    FLUID_USDE_SMART = ("Fluid_usde_smart", "Fluid USDe Smart", Token.USDE)

    # Cork
    CORK_USDE = ("cork_usde", "Cork USDe", Token.USDE)
    CORK_SUSDE = ("cork_susde", "Cork SUSDe", Token.SUSDE)

    # Claimed ENA
    CLAIMED_ENA_EXAMPLE = ("claimed_ena_example", "Claimed ENA Example", Token.ENA)
    BEEFY_CACHED_BALANCE_EXAMPLE = (
        "beefy_cached_balance_example",
        "Beefy Cached Balance Example",
        Token.USDE,
    )

    # Zerolend
    ZEROLEND_SUSDE = ("zerolend_susde_deposit","Zerolend sUSDe",Token.SUSDE)
    ZEROLEND_USDE = ("zerolend_usde_deposit", "Zerolend USDe", Token.USDE)

    KAMINO_SUSDE_COLLATERAL_EXAMPLE = (
        "kamino_susde_collateral_example",
        "Kamino sUSDe Collateral Example",
        Token.SUSDE,
    )

    RATEX_USDE_EXAMPLE = ("ratex_usde_example", "Ratex USDe Example", Token.USDE)

    # Upshift sUSDe
    UPSHIFT_UPSUSDE = ("upshift_upsusde", "Upshift upsUSDe", Token.SUSDE)

    # Tempest Finance
    TEMPEST_SWELL_USDE = (
        "tempest_swell_usde_held",
        "Tempest Swell USDe",
        Token.USDE,
    )

    # agni
    AGNI = (
        "agni",
        "Agni",
        Token.USDE,
    )

    # Rumpel
    RUMPEL_SENA_LP = (
        "rumpel_kpsats3_sena_lp_held",
        "Rumpel kpSATS-3/sENA LP",
        Token.SENA
    )

    # InfinityPools
    INFINITYPOOLS = (
        "infinityPools",
        "InfinityPools",
        Token.SUSDE,
    )
    # Venus
    VENUS_SUSDE = ("venus_susde", "Venus sUSDe", Token.SUSDE)

    # Bulbaswap
    BULBASWAP = (
        "bulbaswap",
        "Bulbaswap",
        Token.USDE,
    )

    def __init__(self, column_name: str, description: str, token: Token = Token.USDE):
        self.column_name = column_name
        self.description = description
        self.token = token

    def get_column_name(self) -> str:
        return self.column_name

    def get_description(self) -> str:
        return self.description

    def get_token(self) -> Token:
        return self.token
