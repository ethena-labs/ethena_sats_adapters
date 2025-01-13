import * as dotenv from "dotenv";
import {
  Aptos,
  AptosConfig,
  Network,
  WriteSetChangeWriteResource,
  isUserTransactionResponse,
  MoveResource,
} from "@aptos-labs/ts-sdk";

dotenv.config();

const config = new AptosConfig({ network: Network.MAINNET });
// Aptos is the main entrypoint for all functions
const client = new Aptos(config);

const args = process.argv.slice(2);
const SUSDE_LPT_METADATA = args[0];
const decimals = Number(args[1]);
const block = Number(args[2]);
const user_balances: Record<string, number> = new Proxy(
  args[3] ? JSON.parse(args[3]) : {},
  {
    get: (target, prop) => target[prop] || 0,
  }
);

type FungibleStoreResource = WriteSetChangeWriteResource & {
  data: MoveResource<FungibleStoreData>;
};

type ObjectCoreResource = WriteSetChangeWriteResource & {
  data: MoveResource<ObjectCoreData>;
};

type FungibleStoreData = {
  balance: string;
  metadata: {
    inner: string;
  };
};

type ObjectCoreData = {
  owner: string;
};

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

  for (const transaction of user_transactions) {
    // First, collect all ObjectCore and LPT changes
    const objectCoreChanges = new Map<string, string>();
    const lptChanges: Array<{ store: string; balance: string }> = [];

    // Collect all relevant changes
    for (const change of transaction.changes as WriteSetChangeWriteResource[]) {
      if (isObjectCoreChange(change)) {
        objectCoreChanges.set(change.address, change.data.data.owner);
      } else if (isLPTFungibleStoreChange(change)) {
        lptChanges.push({
          store: change.address,
          balance: change.data.data.balance,
        });
      }
    }

    // Process LPT changes after we have all the data
    for (const { store, balance } of lptChanges) {
      const userAddress = objectCoreChanges.get(store);
      if (userAddress) {
        user_balances[userAddress] = scaleDownByDecimals(
          Number(balance),
          decimals
        );
      }
    }
  }

  console.log(
    JSON.stringify({
      balances: user_balances,
    })
  );
}

function scaleDownByDecimals(value: number, decimals: number) {
  return value / 10 ** decimals;
}

function isLPTFungibleStoreChange(
  change: WriteSetChangeWriteResource
): change is FungibleStoreResource {
  return (
    change.type === "write_resource" &&
    change.data.type === "0x1::fungible_asset::FungibleStore" &&
    (change as FungibleStoreResource).data.data.metadata.inner ===
      SUSDE_LPT_METADATA
  );
}

function isObjectCoreChange(
  change: WriteSetChangeWriteResource
): change is ObjectCoreResource {
  return (
    change.type === "write_resource" &&
    change.data.type === "0x1::object::ObjectCore"
  );
}

const strategy = getStrategy().catch(console.error);
