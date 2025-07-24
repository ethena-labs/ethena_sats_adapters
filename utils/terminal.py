from constants.terminal import TUSDE_DECIMALS

def convert_to_decimals(value: int) -> float:
    return value / (10 ** TUSDE_DECIMALS)