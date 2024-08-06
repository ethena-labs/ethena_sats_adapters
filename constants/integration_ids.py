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
    
    #PENPIE 
    PENPIE_SUSDE_JULY_LPT=('penpie_susde_july_effective_lpt_held', 'PENPIE sUSDe July LPT', Token.SUSDE)
    PENPIE_Karak_sUSDe_26SEP2024_LPT= ('PENPIE_Karak_sUSDe_26SEP2024_effective_lpt_held', 'Karak_sUSDe_26SEP2024', Token.SUSDE)
    PENPIE_Karak_USDE_26SEP2024_LPT= ('PENPIE_Karak_USDE_26SEP2024_effective_lpt_held', 'Karak_USDE_26SEP2024', Token.USDE)
    PENPIE_sUSDe25APR2024_LPT= ('PENPIE_sUSDe25APR2024_effective_lpt_held', 'sUSDe25APR2024', Token.SUSDE)
    PENPIE_sUSDe26SEP2024_LPT= ('PENPIE_sUSDe26SEP2024_effective_lpt_held', 'sUSDe26SEP2024', Token.SUSDE)
    PENPIE_USDe25JUL2024_LPT= ('PENPIE_USDe25JUL2024_effective_lpt_held', 'USDe25JUL2024', Token.USDE)
    PENPIE_Zircuit_USDe27JUN2024_LPT= ('PENPIE_Zircuit_USDe27JUN2024_effective_lpt_held', 'Zircuit_USDe27JUN2024', Token.USDE)
    PENPIE_ENA29AUG2024_LPT= ('PENPIE_ENA29AUG2024_effective_lpt_held', 'ENA29AUG2024', Token.ENA)
    PENPIE_USDE_ARB_AUG2024_LPT= ('PENPIE_USDE_ARB_AUG2024_effective_lpt_held', 'USDE_ARB_AUG2024', Token.USDE)
    

    # EQUILIBRIA
    EQUILIBRIA_SUSDE_SEPT_LPT = ('equilibria_susde_sept_effective_lpt_held', 'Equilibria sUSDe Sept LPT', Token.SUSDE)
    EQUILIBRIA_Karak_SUSDE_SEPT_SEPT = ('equilibria_karak_susde_sept_effective_lpt_held', 'Equilibria Karak sUSDe Sept LPT', Token.SUSDE)
    EQUILIBRIA_Karak_USDE_SEPT_LPT = ('equilibria_karak_usde_sept_effective_lpt_held', 'Equilibria Karak USDe Sept LPT', Token.USDE)
    EQUILIBRIA_Zircuit_USDE_AUG_LPT = ('equilibria_zircuit_usde_aug_effective_lpt_held', 'Equilibria Zircuit USDe Aug LPT', Token.USDE)
    EQUILIBRIA_rUSDE_SEPT_LPT = ('equilibria_rusde_sept_effective_lpt_held', 'Equilibria rUSDe Sept LPT')
    EQUILIBRIA_USDE_LPT_EXPIRY = ('equilibria_usde_lpt_expiry_effective_lpt_held', 'Equilibria USDe LPT Expiry', Token.USDE)
    EQUILIBRIA_SUSDE_APR_EXPIRY = ('equilibria_susde_apr_expiry_effective_lpt_held', 'Equilibria sUSDe Apr Expiry', Token.SUSDE)
    
    # Term Finance
    TERM_SUSDE = ('term_susde_held', 'Term Finance sUSDe', Token.SUSDE)

    # Synthetix
    SYNTHETIX_USDE_LP = ('synthetix_usde_arb_lp_bal', 'Synthetix V3 Arbitrum USDe LP', Token.USDE)

    # Lendle
    LENDLE_USDE_LPT = ('lendle_usde_lpt_bal', 'Lendle Mantle USDe LPT', Token.USDE)
    
    # Lyra
    LYRA_SUSDE_BULL_MAINNET = ("lyra_susde_bull_mainnet", "Lyra sUSDe Bull Vault Mainnet", Token.SUSDE)
    LYRA_SUSDE_BULL_ARBITRUM = ("lyra_susde_bull_arbitrum", "Lyra sUSDe Bull Vault Arbitrum", Token.SUSDE)
    # Velodrome
    VELODROME_MODE_USDE = ('velodrome_mode_usde', 'Velodrome Mode USDe', Token.USDE)
    VELODROME_MODE_SUSDE = ('velodrome_mode_susde', 'Velodrome Mode sUSDe', Token.SUSDE)
    # Ambient
    AMBIENT_SCROLL_LP = ('ambient_usde_scroll_lp_bal', 'Ambient Scroll LP', Token.USDE)
    
    # Nuri
    NURI_USDE_LP = ('nuri_usde_lp_bal', 'Nuri USDe LP', Token.USDE)

    # Merchant Moe
    MERCHANT_MOE_METH_USDE_LBT = ('merchant_moe_in_range_lbt_liq_held', "Merchant Moe mETH/USDe Liquidity Book Token")
    # Rho Markets
    RHO_MARKETS_USDE_LP = ('rho_markets_usde_scroll_lp_bal', 'Rho Markets Scroll USDe LP', Token.USDE)

    # Splice
    SPLICE_USDE_YT = ('splice_usde_yt', 'Splice USDe YT', Token.USDE)
    SPLICE_USDE_LPT = ('splice_usde_lpt', 'Splice USDe LPT', Token.USDE)
    SPLICE_SUSDE_YT = ('splice_susde_yt', 'Splice SUSDe YT', Token.SUSDE)
    SPLICE_SUSDE_LPT = ('splice_susde_lpt', 'Splice SUSDu LPT', Token.SUSDE)

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
