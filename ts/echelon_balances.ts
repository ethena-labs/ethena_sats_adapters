import * as dotenv from "dotenv";
import {
  Aptos,
  AptosConfig,
  Network,
  isUserTransactionResponse,
} from "@aptos-labs/ts-sdk";

dotenv.config();

const config = new AptosConfig({ network: Network.MAINNET });
// Aptos is the main entrypoint for all functions
const client = new Aptos(config);

const args = process.argv.slice(2);
const LENDING_CONTRACT_ADDRESS = args[0];
const market_address = args[1];
const decimals = Number(args[2]);
const block = Number(args[3]);
const user_balances: Record<string, number> = new Proxy(
  args[4] ? JSON.parse(args[4]) : {},
  {
    get: (target, prop) => target[prop] || 0,
  }
);

async function getStrategy() {
  const block_data = await client.getBlockByHeight({
    blockHeight: block,
    options: {
      withTransactions: true,
    },
  });

  if (!block_data) {
    throw new Error(`Block ${block} not found`);
  }

  if (!block_data.transactions) {
    throw new Error(`No transactions found in Block ${block}`);
  }

  const user_transactions = block_data.transactions.filter(
    isUserTransactionResponse
  );

  // fetch exchange rate from echelon for the current block
  const [exchange_rate_numerator, exchange_rate_denominator] =
    await client.view({
      payload: {
        function: `${LENDING_CONTRACT_ADDRESS}::lending::exchange_rate`,
        functionArguments: [market_address],
      },
      options: { ledgerVersion: Number(block_data.last_version) },
    });
  const exchange_rate =
    Number(exchange_rate_numerator) / Number(exchange_rate_denominator);

  // iterate over all transactions and find all echelon events
  for (const transaction of user_transactions) {
    const echelon_events = transaction.events.filter(isEchelonEvent);

    // iterate over all echelon events and update user balances with the differentials
    for (const event of echelon_events) {
      let user_address: string;
      let user_shares: number;

      if (isSupplyEvent(event)) {
        user_address = event.data.account_addr;
        user_shares = Number(event.data.user_shares);
      } else if (isWithdrawEvent(event)) {
        user_address = event.data.account_addr;
        user_shares = Number(event.data.user_shares);
      } else if (isLiquidateEvent(event)) {
        user_address = event.data.borrower_addr;
        user_shares = Number(event.data.borrower_shares);
      } else {
        continue;
      }

      user_balances[user_address] =
        scaleDownByDecimals(user_shares, decimals) * exchange_rate;
    }
  }

  console.log(JSON.stringify(user_balances));
}

function scaleDownByDecimals(value: number, decimals: number) {
  return value / 10 ** decimals;
}

function isSupplyEvent(event: any) {
  return (
    event.type.includes("SupplyEvent") &&
    event.data.market_obj.inner === market_address
  );
}

function isWithdrawEvent(event: any) {
  return (
    event.type.includes("WithdrawEvent") &&
    event.data.market_obj.inner === market_address
  );
}

function isLiquidateEvent(event: any) {
  return (
    event.type.includes("LiquidateEvent") &&
    event.data.collateral_market_obj.inner === market_address
  );
}

function isEchelonEvent(event: any) {
  return event.type.includes(`${LENDING_CONTRACT_ADDRESS}::lending::`);
}

const strategy = getStrategy().catch(console.error);
