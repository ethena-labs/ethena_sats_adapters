import * as dotenv from "dotenv";
import { Aptos, AptosConfig, Network } from "@aptos-labs/ts-sdk";

dotenv.config();

const config = new AptosConfig({ network: Network.MAINNET });
// Aptos is the main entrypoint for all functions
const client = new Aptos(config);

const args = process.argv.slice(2);
const LENDING_CONTRACT_ADDRESS = args[0];
const market_address = args[1];
const decimals = Number(args[2]);
const block = Number(args[3]);
const user_addresses: Array<string> = JSON.parse(args[4]);

async function getStrategy() {
  // iterate over all users and get their susde balance
  const user_balances: Record<string, number> = {};
  for (const address of user_addresses) {
    const susde_balance = await client.view({
      payload: {
        function: `${LENDING_CONTRACT_ADDRESS}::lending::account_coins`,
        functionArguments: [address, market_address],
      },
      options: { ledgerVersion: block },
    });

    user_balances[address] = scaleDownByDecimals(
      Number(susde_balance),
      decimals
    );
  }

  console.log(JSON.stringify(user_balances));
}

function scaleDownByDecimals(value: number, decimals: number) {
  return value / 10 ** decimals;
}

const strategy = getStrategy().catch(console.error);
