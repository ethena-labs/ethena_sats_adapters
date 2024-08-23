import json
from dataclasses import dataclass

from constants.chains import Chain
from constants.summary_columns import SummaryColumn
from constants.curve import RewardContractConfig

from models.integration import Integration

from utils.web3_utils import (
    W3_BY_CHAIN, 
    fetch_events_logs_with_retry, 
    call_with_retry,
    multicall,
)

@dataclass(frozen=True)
class UserState:
    address: str
    state: tuple
    block: int
    
    def __init__(self, address: str, state: list, block: int):
        object.__setattr__(self, 'address', address)
        object.__setattr__(self, 'state', tuple(state))
        object.__setattr__(self, 'block', block)

    def __hash__(self):
        return hash((self.address, self.state, self.block))


class Curve(Integration):
    """
    Base class for Curve integrations.    
    """

    def __init__(
        self, 
        reward_config: RewardContractConfig,
    ):
        """
        Initialize the Curve integration.

        Args:
            reward_config (RewardContractConfig): The configuration for the reward contract.
        """
        
        super().__init__(
            integration_id=reward_config.integration_id,
            start_block=reward_config.genesis_block,
            chain=reward_config.chain,
            summary_cols=SummaryColumn.CURVE_LLAMALEND_SHARDS,
        )
        
        self.w3 = W3_BY_CHAIN[self.chain]["w3"]
        self.reward_config = reward_config
        with open(self.reward_config.abi_filename, "r") as f:
            abi = json.load(f)
            self.contract = self.w3.eth.contract(
                address=self.reward_config.address,
                abi=abi
            )
        self.contract_function = self.contract.functions.user_state
        self.contract_event = self.contract.events.Borrow()
        self.start_state: List[UserState] = []
        self.last_indexed_block: int = 0
            
    def get_balance(self, user: str, block: int) -> float:
        """
        Retrieve the collateral balance for a user at a specific block.

        Args:
            user (str): EVM address of the user.
            block (int): Block number to query the balance at.

        Returns:
            float: The user's collateral balance in wei.
        """
        return self.get_user_state(user, block)[self.reward_config.state_arg_no]
        
    def get_user_states(self, block: int) -> list:
        """
        Retrieve user states for all participants at a specific block.

        Args:
            block (int): Block number to query the balances at.

        Returns:
            List[Tuple[str, float]]: A list of tuples containing (address, balance) pairs.
        """

        self.get_participants()  # Ensure participants list is up to date

        calls = [
            (self.contract, self.contract_function.fn_name, [user_info.address])
            for user_info in self.start_state
        ]
        results = multicall(self.w3, calls, block)

        states = []
        for user_info, result in zip(self.start_state, results):
            states.append(
                UserState(
                    address=user_info.address,
                    state=result[self.reward_config.state_arg_no],
                    block=block
                )
            )

        return states
    
    def get_user_state(self, user: str, block: int) -> float:
        """
        Retrieve the collateral balance for a user at a specific block.

        Args:
            user (str): EVM address of the user.
            block (int): Block number to query the balance at.

        Returns:
            float: The user's collateral balance in wei.
        """
        return call_with_retry(
            self.contract_function(user),
            block,
        )
        
    def get_current_block(self) -> int:
        return self.w3.eth.get_block_number()

    def get_participants(self) -> list:
        """
        Fetch all participants who have borrowed from the LlamaLend market.

        Returns:
            list: A list of unique Ethereum addresses that have borrowed.
        """
        page_size = 50000
        current_block = self.get_current_block()
        if self.last_indexed_block == current_block:
            return [user_info.address for user_info in self.start_state]

        start_block = max(self.start_block, self.last_indexed_block + 1)

        all_users = set()
        while start_block <= current_block:
            to_block = min(start_block + page_size, current_block)
            events = fetch_events_logs_with_retry(
                f"Curve LlamaLend {self.chain.name} {self.integration_id.get_description()} "
                f"market borrowers from its genesis block "
                f"({start_block}) to the current block ({to_block})",
                self.contract_event,
                start_block,
                to_block,
            )
            for event in events:
                user = event["args"][self.reward_config.event_arg_name]
                all_users.add(
                    UserState(
                        address=user,
                        state=self.get_user_state(user, current_block),
                        block=event["blockNumber"],
                    )
                )
            start_block += page_size

        self.start_state.extend(all_users)
        self.last_indexed_block = current_block
        
        return [user_info.address for user_info in self.start_state]
