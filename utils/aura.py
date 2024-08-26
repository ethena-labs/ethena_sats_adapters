
import logging
import json

from constants.chains import Chain
from constants.integration_ids import IntegrationID
from constants.aura import (
  L1_USDE_ADDRESS,
  L1_SUSDE_ADDRESS,
  L2_USDE_ADDRESS,
  L2_SUSDE_ADDRESS,
  AURA_CONSTANTS,
)
from models.integration import Integration
from utils.web3_utils import (
  fetch_events_logs_with_retry,
  call_with_retry,
  w3_arb,
  w3,
  w3_fraxtal,
)

with open("abi/aura_booster_lite.json") as f:
  booster_abi = json.load(f)

with open("abi/aura_base_reward.json") as f:
  base_reward_abi = json.load(f)

with open("abi/balancer_composable_stable_pool.json") as f:
  lp_token_abi = json.load(f)

with open("abi/balancer_vault.json") as f:
  balancer_vault_abi = json.load(f)




class AuraFinanceIntegration(Integration):
  def __init__(
    self,
    pool_id: int,
    crv_rewards_address: str,
    start_block: int,
    chain: Chain = Chain.ETHEREUM,
  ):
    super().__init__(
      IntegrationID.AURA_USDE,
      start_block,
      chain,
      None, # list of SummaryColumn enums
      20, # sats multiplier for the protocol that has been agreed upon
      1,
      None, # excluded addresses
      None, # end block
      None, # reward multiplier function
    )

    try:
      constants = AURA_CONSTANTS[chain]
    except KeyError:
      raise KeyError(f"Aura finance not deployed on chain {chain}")

    self.pool_id = pool_id

    self.w3 = w3
    if chain == Chain.ARBITRUM:
      self.w3 = w3_arb
    elif chain == Chain.FRAXTAL:
      self.w3 = w3_fraxtal

    self.booster_contract = self.w3.eth.contract(address=constants["aura_booster_address"], abi=booster_abi)
    self.balancer_vault_contract = self.w3.eth.contract(address=constants["balancer_vault_address"], abi=balancer_vault_abi)
    self.crv_rewards_contract = self.w3.eth.contract(address=crv_rewards_address, abi=base_reward_abi)
    pool_info = call_with_retry(
      self.booster_contract.functions.poolInfo(pool_id),
      "latest",
    )
    self.lp_token_contract = self.w3.eth.contract(address=pool_info[0], abi=lp_token_abi)

    self.usde_address = L1_USDE_ADDRESS
    self.susde_address = L1_SUSDE_ADDRESS
    if chain != Chain.ETHEREUM:
      self.usde_address = L2_USDE_ADDRESS
      self.susde_address = L2_SUSDE_ADDRESS


  def get_balance(self, user: str, block: int) -> float:
    user_balance = call_with_retry(
      self.crv_rewards_contract.functions.balanceOf(user),
      block,
    )
    lp_supply = call_with_retry(
      self.lp_token_contract.functions.getActualSupply(),
      block,
    )
    pool_id = call_with_retry(
      self.lp_token_contract.functions.getPoolId(),
      block,
    )
    pool_tokens = call_with_retry(
      self.balancer_vault_contract.functions.getPoolTokens(pool_id),
      block,
    )
    token_addresses = [address.lower() for address in pool_tokens[0]]
    usde_index = -1
    try:
      usde_index = token_addresses.index(self.usde_address)
    except ValueError:
      try:
        usde_index = token_addresses.index(self.susde_address)
      except ValueError:
        logging.error(f"USDE and SUSDE not found in pool {pool_id.hex()}")
        return 0
    usde_amount = pool_tokens[1][usde_index]
    return user_balance / lp_supply * usde_amount

  def get_participants(self) -> list:
    if self.participants is not None:
      return self.participants

    logging.info(f"[{self.integration_id.get_description()}] Getting participants...")
    self.participants = self.get_aura_participants()
    logging.info(
      f"[{self.integration_id.get_description()}] Found {len(self.participants)} participants"
    )
    return self.participants

  def get_aura_participants(self):
    all_users = set()

    start = self.start_block
    page_size = 10_000
    target_block = self.w3.eth.get_block_number()
    while start < target_block:
      to_block = min(start + page_size, target_block)
      deposits = fetch_events_logs_with_retry(
        f"AURA users {self.crv_rewards_contract.address}",
        self.crv_rewards_contract.events.Staked(),
        start,
        to_block,
      )
      print(start, to_block, len(deposits), "getting AURA Reward Staked events")

      for deposit in deposits:
        all_users.add(deposit["args"]["user"])
      start += page_size

    return all_users


if __name__ == "__main__":
  integration = AuraFinanceIntegration()
  print(integration.get_participants())
  # print(integration.get_balance("0x9c18F6EB2144cB61Af7614D7437D61bFeD688D9B", "latest"))