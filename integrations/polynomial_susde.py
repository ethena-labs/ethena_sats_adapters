from constants.chains import Chain
from integrations.integration import Integration
from integrations.integration_ids import IntegrationID
from utils.web3_utils import w3_polynomial, fetch_events_logs_with_retry, call_with_retry
from utils.polynomial import core_proxy_contract, core_account_proxy_contract, owner_register_contract
from constants.polynomial import POLYNOMIAL_DEPLOYMENT_BLOCK, POLYNOMIAL_USDE_TOKEN_ADDRESS, POLYNOMIAL_DEPLOYER_ADDRESS, POLYNOMIAL_BYTECODE_HASH  
from eth_utils import keccak, remove_0x_prefix
from web3 import Web3
import requests

class PolynomialIntegration(Integration): 
      def __init__(self):
        super().__init__(
            IntegrationID.POLYNOMIAL_SUSDE,
            POLYNOMIAL_DEPLOYMENT_BLOCK,
            Chain.POLYNOMIAL,
            [],
            5,
            1,
            None,
            None,
        )


      def get_balance(self, user: str, block: int) -> float:
        scw_address = get_scw_address_from_eoa(user)
        scw_address = Web3.to_checksum_address(scw_address)  

        total_balance = 0
        try:
            account_id = call_with_retry(
                core_account_proxy_contract.functions.tokenOfOwnerByIndex(scw_address, 0),
                block,
            )
            _, balance, _ = call_with_retry(
                core_proxy_contract.functions.getAccountCollateral(
                    account_id, POLYNOMIAL_USDE_TOKEN_ADDRESS
                ),
                 block,
            )
            total_balance += balance
        except Exception as e:
            pass

        return total_balance / 1e18


      def get_participants(self, blocks: list[int] | None) -> set[str]:
        page_size = 19000
        start_block = POLYNOMIAL_DEPLOYMENT_BLOCK
        target_block = w3_polynomial.eth.get_block_number()

        all_users: set[str] = set()
        registered_users: set[str] = set()

        while start_block < target_block:
            to_block = min(start_block + page_size, target_block)
            transfers = fetch_events_logs_with_retry(
                f"Polynomial users from {start_block} to {to_block}",
                core_account_proxy_contract.events.Transfer(),
                start_block,
                to_block,
            )
            for transfer in transfers:
                all_users.add(transfer["args"]["to"])
            
            start_block += page_size

        # Fetch all owner registered events
        owner_registered_events = fetch_events_logs_with_retry(
            f"Polynomial OwnerRegistered events from {POLYNOMIAL_DEPLOYMENT_BLOCK} to {target_block}",
            owner_register_contract.events.OwnerRegistered(),
            POLYNOMIAL_DEPLOYMENT_BLOCK,
            target_block
        )

        for event in owner_registered_events:
            owner_address = event["args"]["owner"]
            kernel_address = event["args"]["kernel"]
            if kernel_address in all_users:
                all_users.remove(kernel_address)
                registered_users.add(owner_address)

       
        unregistered_users = all_users
        addresses_json = {"accounts": list(unregistered_users)}
        
        response = requests.post(
             "https://perps-api-mainnet.polynomial.finance/core/zerodev-accounts/owners",
             json=addresses_json
         )

        if response.status_code == 201:
            response_data = response.json()
           
            api_owners = set()
            for entry in response_data:
                if "owner" in entry:
                    api_owners.add(entry["owner"])
            
        else:
            api_owners = set()

        combined_owners = registered_users.union(api_owners)
        self.participants = combined_owners
        return combined_owners

def get_scw_address_from_eoa(eoa_address: str) -> str:
    w3 = Web3()
    
    fn_signature = 'initialize(bytes21,address,bytes,bytes,bytes[])'
    fn_selector = keccak(text=fn_signature)[:4].hex()
    
    init_args = [
        '0x01845ADb2C711129d4f3966735eD98a9F09fC4cE57', 
        '0x0000000000000000000000000000000000000000',     
        eoa_address,                                       
        '0x',                                             
        []                                                
    ]
    
    init_data = w3.eth.codec.encode(
        ['bytes21', 'address', 'bytes', 'bytes', 'bytes[]'],
        init_args
    )
    init_data = '0x' + fn_selector + init_data.hex()
    
    encoded_index = '0x' + '0' * 60 + hex(8008)[2:]  # Adjust padding to match TypeScript
    
    concat_hex = init_data + encoded_index[2:]
    salt = keccak(hexstr=remove_0x_prefix(concat_hex))
    
  
    create2_input = (
        b'\xff' +
        bytes.fromhex(remove_0x_prefix(POLYNOMIAL_DEPLOYER_ADDRESS)) +
        salt +  
        bytes.fromhex(remove_0x_prefix(POLYNOMIAL_BYTECODE_HASH))
    )
    
    result_address = '0x' + keccak(create2_input)[12:].hex()
    
    return result_address

if __name__ == "__main__":
    polynomial = PolynomialIntegration()
    participants = polynomial.get_participants(None)
    print(len(participants))
    print(polynomial.get_balance(list(participants)[0], 9415666))