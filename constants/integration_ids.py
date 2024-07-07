from enum import Enum

from constants.integration_token import Token


class IntegrationID(Enum):
    EXAMPLE = ('example', 'Example', Token.USDE)
    PENDLE_USDE_LPT = ('pendle_effective_lpt_held', 'Pendle USDe LPT')
    PENDLE_USDE_YT = ('pendle_yt_held', 'Pendle USDe YT')
    PENDLE_SUSDE_LPT_APRIL_EXPIRY = ('pendle_effective_susde_apr_lpt_held', 'Pendle sUSDe LPT (April expiry)', Token.SUSDE)
    PENDLE_SUSDE_YT_APRIL_EXPIRY = ('pendle_susde_apr_yt_held', 'Pendle sUSDe YT (April expiry)', Token.SUSDE)
    PENDLE_SUSDE_LPT_JULY_EXPIRY = ('pendle_effective_susde_jul_lpt_held', 'Pendle sUSDe LPT (July expiry)', Token.SUSDE)
    PENDLE_SUSDE_YT_JULY_EXPIRY = ('pendle_susde_jul_yt_held', 'Pendle sUSDe YT (July expiry)', Token.SUSDE)
    PENDLE_SUSDE_LPT_SEPT_EXPIRY = ('pendle_effective_susde_sep_lpt_held', 'Pendle sUSDe LPT (Sept expiry)', Token.SUSDE)
    PENDLE_SUSDE_YT_SEPT_EXPIRY = ('pendle_susde_sep_yt_held', 'Pendle sUSDe YT (Sept expiry)', Token.SUSDE)
    PENDLE_ENA_LPT = ('pendle_effective_ena_lpt_held', 'Pendle ENA LPT', Token.ENA)
    PENDLE_ENA_YT = ('pendle_ena_yt_held', 'Pendle ENA YT', Token.ENA)
    PENDLE_ARBITRUM_USDE_LPT = ('pendle_arbtrium_effective_lpt_bal', 'Pendle Arbitrum USDe LPT')
    PENDLE_ARBITRUM_USDE_YT = ('pendle_arbtrium_yt_bal', 'Pendle Arbitrum USDe YT')
    PENDLE_KARAK_USDE_LPT = ('pendle_karak_usde_lpt_held', 'Pendle Karak USDe LPT')
    PENDLE_KARAK_USDE_YT = ('pendle_karak_usde_yt_held', 'Pendle Karak USDe YT')
    PENDLE_KARAK_SUSDE_LPT = ('pendle_karak_susde_lpt_held', 'Pendle Karak sUSDe LPT', Token.SUSDE)
    PENDLE_KARAK_SUSDE_YT = ('pendle_karak_susde_yt_held', 'Pendle Karak sUSDe YT', Token.SUSDE)
    PENDLE_MANTLE_USDE_LPT = ('pendle_mantle_effective_lpt_bal', 'Pendle Mantle USDe LPT')
    PENDLE_MANTLE_USDE_YT = ('pendle_mantle_yt_bal', 'Pendle Mantle USDe YT')
    PENDLE_ZIRCUIT_USDE_LPT = ('pendle_effective_zircuit_usde_lpt_held', 'Pendle Zircuit USDe LPT')
    PENDLE_ZIRCUIT_USDE_YT = ('pendle_zircuit_usde_yt_held', 'Pendle Zircuit USDe YT')

    # Stake DAO
    STAKEDAO_SUSDE_JULY_LPT = ('stakedao_susde_july_effective_lpt_held', 'Stake DAO sUSDe July LPT', Token.SUSDE)
    STAKEDAO_SUSDE_SEPT_LPT = ('stakedao_susde_sept_effective_lpt_held', 'Stake DAO sUSDe Sept LPT', Token.SUSDE)
    STAKEDAO_USDE_JULY_LPT = ('stakedao_usde_july_effective_lpt_held', 'Stake DAO USDe July LPT', Token.USDE)

    # Synthetix
    SYNTHETIX_USDE_LP = ('synthetix_usde_arb_lp_bal', 'Synthetix V3 Arbitrum USDe LP', Token.USDE)

    # Rho Markets
    RHO_MARKETS_USDE_LP = ('rho_markets_usde_scroll_lp_bal', 'Rho Markets Scroll USDe LP', Token.USDE)

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
