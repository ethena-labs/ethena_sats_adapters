# Overview

This repo offers a self service approach to Ethena Points Campaign integrations.

# Instructions

For your protocol to be included and your users to receive points, you should submit a PR to this repo. Here some guidelines to follow:

1. Make a copy of `.env.example` and name it `.env`.
2. Run `pip install -r requirements.txt` to install the required packages.
3. Add your integration metadata to `integrations/integration_ids.py`.
4. Add your integration metadata to `constants/summary_columns.py`.
5. Make a copy of `integrations/template.py`, naming the file `[protocol name]_integration.py` and place in the `integrations` directory.
6. Your integration must be a class that inherits from `CachedBalancesIntegration` and implements the `get_block_balances` method.
6. The `get_block_balances` method should return a dict of block numbers to a dict of user addresses to balances at that block.
7. Write some basic tests at the bottom of the file to ensure your integration is working correctly.
8. Submit a PR to this repo with your integration and ping the Ethena team in Telegram.

# Guidelines

- Integrations must follow this architecture and be written in python.
- Pendle integrations are included as examples of functioning integrations. Run `python -m integrations.pendle_lpt_integration` to see the output.
- The `get_block_balances` method should be as efficient as possible.
- We prefer that on chain RPC calls are used to get information as much as possible due to reliability and trustlessness. Off chain calls to apis or subgraphs are acceptable if necessary. If usage is not reasonable or the external service is not reliable, users may not receive their sats.
