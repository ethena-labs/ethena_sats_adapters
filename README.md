# Overview

This repo offers a self service approach to Ethena Sats Campaign integrations.

# Instructions

For your protocol to be included and your users to receive sats, you should submit a PR to this repo. Here some guidelines to follow:

1. Make a copy of `.env.example` and name it `.env`.
2. Run `pip install -r requirements.txt` to install the required packages.
3. Add your integration metadata to `integrations/integration_ids.py`.
4. Make a copy of `integrations/template.py`, naming the file `[protocol name].py` and place in the `integrations` directory.
5. Your integration must be a class that inherits from `Integration` and implements the `get_balance` and `get_participants` methods.
6. The `get_balance` method should return the balance of a given user at a given block.
7. The `get_participants` method should return a list of all users that have interacted with the protocol.
8. Write some basic tests at the bottom of the file to ensure your integration is working correctly.
9. Submit a PR to this repo with your integration and ping the Ethena team in Telegram.

# Guidelines

- Integrations must follow this architecture and be written in python.
- Pendle integrations are included as examples of functioning integrations. Run `python -m integrations.pendle_lpt_integration` to see the output.
- The `get_balance` and `get_participants` methods should be as efficient as possible.
- We prefer that on chain RPC calls are used to get information as much as possible due to reliability and trustlessness. For example one could cycle through events for `get_participants` and read from a smart contract for `get_balance`. Off chain calls to apis or subgraphs are acceptable if necessary. If usage is not reasonable or the external service is not reliable, users may not receive their sats.
