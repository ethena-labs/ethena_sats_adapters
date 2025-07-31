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
const user_addresses: string[] = JSON.parse(args[4]);
const XLPT_ORACLE_ADDRESS = args[5];
const SUSDE_USDC_TOKEN_ADDRESS = args[6];

async function getStrategy() {
  // iterate over all users and get their susde balance
  const user_balances: Record<string, number> = {};
  for (const address of user_addresses) {
    const susde_usdc_xlpt_balance = await client.view({
      payload: {
        function: `${LENDING_CONTRACT_ADDRESS}::lending::account_coins`,
        functionArguments: [address, market_address],
      },
      options: { ledgerVersion: block },
    });

    const susde_usdc_xlpt_price = await client.view({
      payload: {
        function: `${XLPT_ORACLE_ADDRESS}::oracle::get_price`,
        functionArguments: [SUSDE_USDC_TOKEN_ADDRESS],
      },
      options: { ledgerVersion: block },
    });

    const susde_usdc_value = Number(susde_usdc_xlpt_balance) * fp64ToFloat(BigInt((susde_usdc_xlpt_price[0] as { v: string }).v));;

    user_balances[address] = scaleDownByDecimals(
      susde_usdc_value,
      decimals
    );
  }

  console.log(JSON.stringify(user_balances));
}

function scaleDownByDecimals(value: number, decimals: number) {
  return value / 10 ** decimals;
}

const ZERO = BigInt(0);
const ONE = BigInt(1);

export const fp64ToFloat = (a: bigint): number => {
  // avoid large number
  let mask = BigInt("0xffffffff000000000000000000000000");
  if ((a & mask) != ZERO) {
    throw new Error("too large");
  }

  // integer part
  mask = BigInt("0x10000000000000000");
  let base = 1;
  let result = 0;
  for (let i = 0; i < 32; ++i) {
    if ((a & mask) != ZERO) {
      result += base;
    }
    base *= 2;
    mask = mask << ONE;
  }

  // fractional part
  mask = BigInt("0x8000000000000000");
  base = 0.5;
  for (let i = 0; i < 32; ++i) {
    if ((a & mask) != ZERO) {
      result += base;
    }
    base /= 2;
    mask = mask >> ONE;
  }
  return result;
};

const strategy = getStrategy().catch(console.error);
