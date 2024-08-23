import sys
sys.path.append("./")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

if __name__ == "__main__":
    from utils.curve import Curve
    from constants.curve import CURVE_LLAMALEND

    console = Console()

    LENDING_CONTRACTS = [Curve(config) for config in CURVE_LLAMALEND]
    console.print(f"Number of contracts: {len(LENDING_CONTRACTS)}", style="bold green")

    for id, contract in enumerate(LENDING_CONTRACTS, start=1):

        # Create a panel with the same width as the table
        panel = Panel(
            f"[bold cyan]{id}. {contract.integration_id.get_description()} on {contract.chain.name}[/bold cyan]",
            expand=False
        )
        console.print(panel)
        console.print(f"Current block in chain {contract.chain.name}: {contract.get_current_block()}")
        console.print(f"Token: {contract.reward_config.integration_id.get_token()}")
        
        # Cache participants
        contract.get_participants()
        
        start_state = contract.start_state
        last_indexed_block = contract.last_indexed_block
        
        console.print(f"Total participants: {len(start_state)}. Balances at latest indexed block {last_indexed_block}:")
        
        latest_state = contract.get_user_states(last_indexed_block)

        console.print("\n")
        table = Table(title="Participant Details")
        table.add_column("Address", style="cyan", no_wrap=True)
        table.add_column("Start Block", justify="right", style="magenta")
        table.add_column("Start Balance", justify="right", style="green")
        table.add_column("Current Balance", justify="right", style="yellow")

        for user_info_start, current_user_info in zip(start_state, latest_state):
            table.add_row(
                user_info_start.address,
                str(user_info_start.block),
                f"{user_info_start.state[0]/1e18:.2f}",
                f"{current_user_info.state[0]/1e18:.2f}",
            )

        console.print(table)
