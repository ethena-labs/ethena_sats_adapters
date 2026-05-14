/**
 * Jupiter Lend borrow vault: aggregate supply-side collateral (raw col amount)
 * per position NFT holder for a single vault.
 *
 * Args: <vault_id | "auto"> <supply_mint> <decimals>
 * - vault_id: numeric vault id on-chain, or "auto" to resolve via lite-api.jup.ag
 *   using the first borrow vault whose supplyToken.address matches supply_mint.
 * - supply_mint: SPL mint of the vault collateral asset (e.g. Ethena USDe / sUSDe).
 * - decimals: human-readable decimal places for JSON output.
 *
 * Uses getVaultsProgram from @jup-ag/lend/borrow plus borrow PDAs from @jup-ag/lend.
 *
 * Env: JUP_LEND_CHUNK_DELAY_MS (default 120 ms between RPC chunks). For smoke tests,
 * JUP_LEND_MAX_POSITIONS caps how many GPA results are processed (omit for full vault).
 */
import * as dotenv from "dotenv";
import { Connection, PublicKey } from "@solana/web3.js";
import BN from "bn.js";
import { SOL_NODE } from "./common";

dotenv.config();

const POSITION_DISCRIMINATOR = Buffer.from([
  170, 188, 143, 228, 122, 64, 247, 208,
]);

const CHUNK = 8;
const CHUNK_DELAY_MS = Number(process.env.JUP_LEND_CHUNK_DELAY_MS ?? 120);

const args = process.argv.slice(2);
const vaultArg = args[0];
const supplyMintStr = args[1];
const decimals = Number(args[2]);

function readU16LE(buf: Buffer, offset: number): number {
  return buf.readUInt16LE(offset);
}

function readU32LE(buf: Buffer, offset: number): number {
  return buf.readUInt32LE(offset);
}

function decodePositionAccount(data: Buffer): {
  vaultId: number;
  positionId: number;
  positionMint: PublicKey;
} {
  const body = data.subarray(8);
  const vaultId = readU16LE(body, 0);
  const positionId = readU32LE(body, 2);
  const positionMint = new PublicKey(body.subarray(6, 6 + 32));
  return { vaultId, positionId, positionMint };
}

async function resolveVaultIdFromApi(supplyMint: string): Promise<number> {
  const { Client } = await import("@jup-ag/lend/api");
  const client = new Client();
  const vaults = await client.borrow.getVaults();
  const want = supplyMint.trim();
  const hit = vaults.find(
    (v: { id: number; supplyToken: { address: string } }) =>
      v.supplyToken.address === want
  );
  if (!hit) {
    throw new Error(
      `No Jupiter Lend borrow vault with supply mint ${want}. ` +
        `Check https://api.solana.fluid.io/v1/ethena/borrowing/vaults or pass an explicit vault id.`
    );
  }
  return hit.id as number;
}

async function getNftHolderWallet(
  connection: Connection,
  positionMint: PublicKey
): Promise<PublicKey> {
  const largest = await connection.getTokenLargestAccounts(positionMint);
  if (!largest.value.length) {
    throw new Error(`No token accounts for mint ${positionMint.toBase58()}`);
  }
  const ta = largest.value[0].address;
  const info = await connection.getParsedAccountInfo(ta);
  const parsed = info.value?.data;
  if (
    !parsed ||
    typeof parsed !== "object" ||
    !("parsed" in parsed) ||
    parsed.parsed.type !== "account"
  ) {
    throw new Error(`Could not parse token account ${ta.toBase58()}`);
  }
  const ownerStr = (parsed.parsed as { info: { owner: string } }).info.owner;
  return new PublicKey(ownerStr);
}

async function main() {
  if (!vaultArg || !supplyMintStr || Number.isNaN(decimals)) {
    throw new Error(
      'Usage: ts-node ts/jup_lend_ethena_vault.ts <vault_id|"auto"> <supply_mint> <decimals>'
    );
  }

  const supplyMint = new PublicKey(supplyMintStr);
  const connection = new Connection(SOL_NODE, "confirmed");

  const [{ borrowPda }, borrowMod] = await Promise.all([
    import("@jup-ag/lend"),
    import("@jup-ag/lend/borrow"),
  ]);
  const { default: baseX } = await import("base-x");
  const bs58 = baseX(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
  );

  const vaultId: number =
    vaultArg === "auto"
      ? await resolveVaultIdFromApi(supplyMintStr)
      : Number(vaultArg);

  if (!Number.isInteger(vaultId) || vaultId < 0) {
    throw new Error(`Invalid vault id: ${vaultArg}`);
  }

  const dummySigner = new PublicKey("11111111111111111111111111111111");
  const program = borrowMod.getVaultsProgram({
    connection,
    signer: dummySigner,
    market: "ethena",
  });

  const vaultConfigPk = borrowPda.getVaultConfig(vaultId);
  const vaultConfig = await program.account.vaultConfig.fetch(vaultConfigPk);
  const cfgSupply = vaultConfig.supplyToken as PublicKey;
  if (!cfgSupply.equals(supplyMint)) {
    throw new Error(
      `Vault ${vaultId} supply token ${cfgSupply.toBase58()} does not match ` +
        `expected ${supplyMint.toBase58()}`
    );
  }

  const vaultIdBytes = Buffer.alloc(2);
  vaultIdBytes.writeUInt16LE(vaultId, 0);

  const accounts = await connection.getProgramAccounts(program.programId, {
    filters: [
      {
        memcmp: {
          offset: 0,
          bytes: bs58.encode(POSITION_DISCRIMINATOR),
        },
      },
      {
        memcmp: {
          offset: 8,
          bytes: bs58.encode(vaultIdBytes),
        },
      },
    ],
  });

  const maxRaw = process.env.JUP_LEND_MAX_POSITIONS;
  const maxN = maxRaw ? Number(maxRaw) : 0;
  const toProcess =
    maxN > 0 && Number.isFinite(maxN) ? accounts.slice(0, maxN) : accounts;

  const out: Record<string, number> = {};

  for (let i = 0; i < toProcess.length; i += CHUNK) {
    const slice = toProcess.slice(i, i + CHUNK);
    await Promise.all(
      slice.map(async ({ pubkey, account }) => {
        let positionId: number;
        let positionMint: PublicKey;
        try {
          const dec = decodePositionAccount(account.data);
          if (dec.vaultId !== vaultId) return;
          positionId = dec.positionId;
          positionMint = dec.positionMint;
        } catch {
          return;
        }

        const posPk = borrowPda.getPosition(vaultId, positionId);
        if (!posPk.equals(pubkey)) {
          return;
        }

        let colRaw: BN;
        try {
          const cur = await borrowMod.getCurrentPosition({
            vaultId,
            positionId,
            connection,
            market: "ethena",
          });
          colRaw = cur.colRaw;
        } catch {
          return;
        }

        if (!colRaw || colRaw.isZero()) return;

        let owner: PublicKey;
        try {
          owner = await getNftHolderWallet(connection, positionMint);
        } catch {
          return;
        }

        const human = colRaw.toNumber() / 10 ** decimals;
        if (human <= 0) return;

        const key = owner.toBase58();
        out[key] = (out[key] ?? 0) + human;
      })
    );
    if (i + CHUNK < toProcess.length && CHUNK_DELAY_MS > 0) {
      await new Promise((r) => setTimeout(r, CHUNK_DELAY_MS));
    }
  }

  console.log(JSON.stringify(out));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
