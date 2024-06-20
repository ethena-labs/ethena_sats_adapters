# Overview

This repo offers a self service approach to Ethena Sats Campaign integrations.  

# Instructions

For your protocol to be included and your users to receive sats, you should submit a PR to this repo.  Here some guidelines to follow:

1. Make a copy of `template.py`, naming the file `[protocol name].py` and place in the `integrations` directory.
2. Your integration must be a class that inherits from `BaseIntegration` and implement the `get_sats` method.

