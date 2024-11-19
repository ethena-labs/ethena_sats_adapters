# Overview

This repo offers a self service approach to Ethena Points Campaign integrations.

# Instructions

For your protocol to be included and your users to receive points, you should submit a PR to this repo. Here some guidelines to follow:

1. Make a copy of `.env.example` and name it `.env`.
2. Run `pip install -r requirements.txt` to install the required packages.
3. Add your integration metadata to `integrations/integration_ids.py`.
4. Create a new summary column in `constants/summary_columns.py`.
5. Make a copy of [Template](integrations/template.py), naming the file `[protocol name]_integration.py` and place in the `integrations` directory.
6. Your integration must be a class that inherits from `CachedBalancesIntegration` and implements the `get_block_balances` method.
7. The `get_block_balances` method should return a dict of block numbers to a dict of user addresses to balances at that block.
8. Write some basic tests at the bottom of the file to ensure your integration is working correctly.
9. Submit a PR to this repo with your integration and ping the Ethena team in Telegram.

# Guidelines

- Integrations must follow this architecture and be written in python.
- Pendle integrations are included as examples of functioning integrations. Run `python -m integrations.pendle_lpt_integration` to see the output.
- The `get_block_balances` method should be as efficient as possible. So the use of the cached data from previous blocks if possible is highly encouraged.
- We prefer that on chain RPC calls are used to get information as much as possible due to reliability and trustlessness. Off chain calls to apis or subgraphs are acceptable if necessary. If usage is not reasonable or the external service is not reliable, users may not receive their sats.

# Example Integrations
- [ClaimedEnaIntegration](integrations/claimed_ena_example_integration.py): This integration demonstrates how to track ENA token claims using cached balance snapshots for improved performance. It reads from previous balance snapshots to efficiently track user claim history.
- [BeefyCachedBalanceExampleIntegration](integrations/beefy_cached_balance_example_integration.py): This integration is an example of a cached balance integration that is based on API calls.
- [PendleLPTIntegration](integrations/pendle_lpt_integration.py): (Legacy Example) A basic integration showing Pendle LPT staking tracking. Note: This is a non-cached implementation included only for reference - new integrations should use the cached approach for better efficiency.
- [PendleYTIntegration](integrations/pendle_yt_integration.py): (Legacy Example) A basic integration showing Pendle YT staking tracking. Note: This is a non-cached implementation included only for reference - new integrations should use the cached approach for better efficiency.
