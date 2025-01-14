import dotenv from "dotenv";
dotenv.config();

export const SOL_NODE =
  process.env.SOLANA_NODE_URL || "https://api.mainnet-beta.solana.com";