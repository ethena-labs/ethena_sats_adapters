import json
from utils.web3_utils import (
    w3,
)
from constants.fluid import vaultResolver, vaultPositionResolver, dexResolver

with open("abi/fluid_vault_resolver.json") as f:
    resolver_abi = json.load(f)
    
with open("abi/fluid_vault_position_resolver.json") as j:
    position_resolver_abi = json.load(j)

with open("abi/fluid_dex_resolver.json") as j:
    dex_resolver_abi = json.load(j)

with open("abi/fluid_smart_lending_resolver.json") as j:
    smart_lending_resolver_abi = json.load(j)

vaultResolver_contract = w3.eth.contract(address=vaultResolver, abi=resolver_abi)
vaultPositionResolver_contract = w3.eth.contract(address = vaultPositionResolver, abi=position_resolver_abi)
dexResolver_contract = w3.eth.contract(address = dexResolver, abi=dex_resolver_abi)
smartLendingResolver_contract = w3.eth.contract(address = smartLendingResolver, abi=smart_lending_resolver_abi)
