import * as dotenv from "dotenv";
import { Connection, PublicKey } from "@solana/web3.js";
import { KaminoMarket } from "@kamino-finance/klend-sdk";
import { SOL_NODE } from "./common";

dotenv.config();

const connection = new Connection(SOL_NODE);

const args = process.argv.slice(2);
const market_address = args[0];
const token_to_filter = args[1];
const decimals = Number(args[2]);

async function getStrategy() {
  const market = await KaminoMarket.load(
    //connection as any, // Type cast to avoid version mismatch
    connection as any,
    new PublicKey(market_address),
    1
  );
  if (!market) {
    throw new Error("Market not found");
  }
  await market.loadReserves();
  await market.refreshAll();
  const obligations = await market.getAllObligationsForMarket();
  const dataMap: Record<string, number> = {};
  for (const i in obligations) {
    const deposits = obligations[i].state.deposits;
    for (const deposit of deposits) {
      if (deposit.depositReserve.toString() == token_to_filter) {
        dataMap[obligations[i].state.owner.toString()] =
          Number(deposit.depositedAmount) / Math.pow(10, decimals);
      }
    }
  }

  console.log(JSON.stringify(dataMap));
}

const strategy = getStrategy().catch(console.error);
