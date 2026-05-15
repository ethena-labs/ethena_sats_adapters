/**
 * Jupiter Lend borrow vault (Ethena market): supply-side collateral per position NFT.
 *
 * Usage:
 *   tsx ts/jup_lend_ethena_vault.ts <vault_state_pubkey> [market]
 *
 * USDE / USDG vault (ethena):
 *   tsx ts/jup_lend_ethena_vault.ts 72RGBXosx2NzHvJyt8AgjRkiX8EyEnT899tfrQSSgNtm ethena
 *
 * Env:
 *   RPC_URL / SOLANA_NODE_URL — Solana RPC (see ts/common.ts)
 *   BATCH_SIZE — accounts per getMultipleAccounts (default 100)
 */
import BN from "bn.js";
import { Connection, PublicKey } from "@solana/web3.js";
import { getVaultsProgram } from "@jup-ag/lend/borrow";
import { borrowPda } from "@jup-ag/lend";
import { SOL_NODE } from "./common";

const EXCHANGE_PRICES_PRECISION = new BN("1000000000000"); // 1e12
const OPERATE_PRECISION = new BN("1000000000"); // 1e9

const [vaultStateArg, marketArg] = process.argv.slice(2);
const vaultStatePk = new PublicKey(
  vaultStateArg ?? "72RGBXosx2NzHvJyt8AgjRkiX8EyEnT899tfrQSSgNtm",
);
const JUPITER_LEND_ETHENA_MARKET = marketArg === "main" ? "main" : "ethena";
const JUPITER_LEND_ETHENA_BATCH_SIZE = Number(process.env.BATCH_SIZE ?? "100");

function rawColToHuman(colRaw: BN, vaultSupplyExchangePrice: BN): number {
  const denom = EXCHANGE_PRICES_PRECISION.mul(OPERATE_PRECISION);
  const rounded = new BN(colRaw.toString())
    .mul(new BN(vaultSupplyExchangePrice.toString()))
    .muln(100)
    .add(denom.divn(2))
    .div(denom);
  return rounded.toNumber() / 100;
}

function chunk<T>(array: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    out.push(array.slice(i, i + size));
  }
  return out;
}

async function main() {
  const connection = new Connection(SOL_NODE);
  const program = getVaultsProgram({ connection, market: JUPITER_LEND_ETHENA_MARKET });

  const vaultState = await program.account.vaultState.fetch(vaultStatePk);

  const vaultId = vaultState.vaultId;
  const nextPositionId = vaultState.nextPositionId;
  const supplyExPrice = vaultState.vaultSupplyExchangePrice;

  const positionIds: number[] = [];
  for (let id = 1; id < nextPositionId; id++) {
    positionIds.push(id);
  }

  const dataMap: Record<string, number> = {};

  for (const ids of chunk(positionIds, JUPITER_LEND_ETHENA_BATCH_SIZE)) {
    const addresses = ids.map((id) =>
      borrowPda.getPosition(vaultId, id, JUPITER_LEND_ETHENA_MARKET),
    );
    const accounts = await program.account.position.fetchMultiple(addresses);

    for (let i = 0; i < ids.length; i++) {
      const position = accounts[i];
      if (!position) continue;

      const supplyRaw = position.supplyAmount;
      if (supplyRaw.isZero()) continue;

      const collateral = rawColToHuman(supplyRaw, supplyExPrice);
      if (collateral <= 0) continue;

      dataMap[String(position.nftId)] = collateral;
    }
  }

  console.log(JSON.stringify(dataMap));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
