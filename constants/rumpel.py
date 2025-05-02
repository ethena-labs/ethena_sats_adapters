import json
from web3 import Web3
from utils.web3_utils import w3
from dataclasses import dataclass

UNIV3_NONFUNGUBLE_POSITION_MANAGER_ADDRESS = Web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88")
SENA_ADDRESS = Web3.to_checksum_address("0x8bE3460A480c80728a8C4D7a5D5303c85ba7B3b9")

with open("abi/univ3_nonfungible_position_manager.json") as f:
    UNIV3_NONFUNGIBLE_POSITION_MANAGER_ABI = json.load(f)
    
UNIV3_NONFUNGIBLE_POSITION_MANAGER_CONTRACT = w3.eth.contract(
    address=UNIV3_NONFUNGUBLE_POSITION_MANAGER_ADDRESS,
    abi=UNIV3_NONFUNGIBLE_POSITION_MANAGER_ABI,
)

with open("abi/univ3_pool.json") as f:
    UNIV3_POOL_ABI = json.load(f)

@dataclass
class KPSATSPool:
    name: str
    deployed_block: int
    kpsats_address: str
    pool_address: str

KPSATS_POOLS = [
    KPSATSPool(
        name="KPSATS3",
        deployed_block=21383217,
        kpsats_address=Web3.to_checksum_address("0x263b0f5e179c1d72B884C43105C620d2112dF2a0"),
        pool_address=Web3.to_checksum_address("0x5D29647b684Ce835F442915cC3C8e99aAb2A26C6")
    ),
    KPSATSPool(
        name="KPSATS4",
        deployed_block=22333279,
        kpsats_address=Web3.to_checksum_address("0x8659c0994C8EC73A66E7587c4c6b3aB38d1223bE"),
        pool_address=Web3.to_checksum_address("0x4d5a1035c8d44163c554ec8027b5db8c819c66b2")
    )
]

