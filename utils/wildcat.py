import json
from utils.web3_utils import W3_BY_CHAIN
from constants.chains import Chain
from web3 import Web3

# TODO: @dillon review kindly please and thankyou im not super confident in this

RAY = 10 ** 27
HALF_RAY = RAY // 2

def rayMul(a: int, b: int) -> int:
    """Multiply two ray-scaled integers and return a ray-scaled integer.

    Implements the same behaviour as the Wildcat TS `rayMul` / Solidity MathUtils.rayMul:
        (a * b + HALF_RAY) / RAY

    Args:
        a: integer value (typically a BigInt from subgraph)
        b: integer value (typically the scaleFactor)

    Returns:
        int: the ray-multiplied result
    """
    
    return (int(a) * int(b) + HALF_RAY) // RAY
