from utils.rho_markets import RhoMarkets
from utils.web3_utils import w3_scroll

if __name__ == "__main__":
    rho_markets = RhoMarkets()
    print(len(rho_markets.get_participants()))
    print(rho_markets.get_balance(
        w3_scroll.to_checksum_address(
            rho_markets.participants[0]),
        7204405))
