import * as dotenv from "dotenv";
import { Aptos, AptosConfig, Network } from "@aptos-labs/ts-sdk";

dotenv.config();

const config = new AptosConfig({ network: Network.MAINNET });
// Aptos is the main entrypoint for all functions
const client = new Aptos(config);

const args = process.argv.slice(2);
const THALA_V1_FARMING_ADDRESS = args[0];
const SUSDE_LPT_PID = args[1];
const decimals = Number(args[2]);
const block = Number(args[3]);
const user_addresses: Array<string> = JSON.parse(args[4]);

async function getStrategy() {
    // iterate over all users and get their susde balance
    const user_balances: Record<string, number> = {};
    for (const address of user_addresses) {
        const [stake_amount, _boosted_stake_amount, _boost_multiplier] = await client.view<string[]>({
            payload: {
                function: `${THALA_V1_FARMING_ADDRESS}::farming::stake_amount`,
                functionArguments: [address, Number(SUSDE_LPT_PID)],
            },
            options: { ledgerVersion: block },
        });

        user_balances[address] = scaleDownByDecimals(
            Number(stake_amount),
            decimals
        );
    }

    console.log(JSON.stringify(user_balances));
}

function scaleDownByDecimals(value: number, decimals: number) {
    return value / 10 ** decimals;
}

const strategy = getStrategy().catch(console.error);