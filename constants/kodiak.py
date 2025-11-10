from enum import Enum

KODIAK_API_URL = "https://staging.backend.kodiak.finance"

class KodiakIslandAddress(Enum):
    USDE = "0xE5A2ab5D2fb268E5fF43A5564e44c3309609aFF9"
    SUSDE = "0xD5B6EA3544a51BfdDa7E6926BdF778339801dFe8"

class Tokens(Enum):
    USDE = "0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"
    SUSDE = "0x211Cc4DD073734dA055fbF44a2b4667d5E5fE5d2"