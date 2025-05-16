import * as dotenv from "dotenv";
import axios from 'axios'
import { Cell } from "@ton/core";

dotenv.config();

const config = {
  tonConsoleBaseUrl: process.env.TON_CONSOLE_BASE_URL || 'https://tonapi.io',
  tonConsoleApiToken: process.env.TON_CONSOLE_API_TOKEN
}

const client = axios.create({
  baseURL: config.tonConsoleBaseUrl,
  headers: config.tonConsoleApiToken
    ? { 'Authorization': `Bearer ${config.tonConsoleApiToken}` }
    : {}
})

const args = process.argv.slice(2);
const contractAddress = args[0];

interface IsFarmixPositionCheckResult {
  is_position: boolean,
  err?: string
  owner_addr?: string
}



async function isContractFarmixPosition() {
  const result: IsFarmixPositionCheckResult = {
    is_position: false
  }

  try {
    const res = await client.get(`v2/blockchain/accounts/${contractAddress}/methods/get_identity`);
    if (!res.data.success || res.data.exit_code !== 0) {
      console.log(JSON.stringify(result))

      return
    }
    const stack = res.data.stack
    const ownerAddrTupleItem = stack[4]
    if (!ownerAddrTupleItem || ownerAddrTupleItem?.type !== 'cell' || !ownerAddrTupleItem.cell) {
      console.log(JSON.stringify(result))

      return
    }
    const ownerAddrCell = Cell.fromHex(ownerAddrTupleItem.cell)
    const ownerAddr = ownerAddrCell.beginParse().loadAddress();

    result.is_position = true;
    result.owner_addr = ownerAddr.toString({ urlSafe: true, bounceable: true  });

    console.log(JSON.stringify(result));
  } catch (err: any) {
    result.err = err?.message ?? 'unknown error'

    console.log(JSON.stringify(result))
  }
}

isContractFarmixPosition();






