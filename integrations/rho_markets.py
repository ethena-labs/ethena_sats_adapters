from utils.rho_markets import RhoMarkets
from utils.web3_utils import w3_scroll

if __name__ == "__main__":
    rho_markets = RhoMarkets()
    participants = rho_markets.get_participants()
    print(len(participants))
    print(
        rho_markets.get_balance(w3_scroll.to_checksum_address(participants[0]), 7751774)
    )
