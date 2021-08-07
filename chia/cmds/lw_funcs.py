import asyncio
import aiosqlite

from chia.full_node.coin_store import CoinStore
from chia.util.db_wrapper import DBWrapper
from chia.types.coin_record import CoinRecord

import sys

from chia.util.bech32m import encode_puzzle_hash
from chia.util.ints import uint32
from chia.util.keychain import Keychain
from chia.wallet.derive_keys import master_sk_to_pool_sk, master_sk_to_wallet_sk
from chia.consensus.coinbase import create_puzzlehash_for_pk

from chia.util.config import load_config
from chia.util.path import path_from_root
from pathlib import Path

async def show(root_path: Path):
    config: Dict = load_config(root_path, "config.yaml")["full_node"]
    db_path_replaced: str = config["database_path"].replace("CHALLENGE", config["selected_network"])
    db_path = path_from_root(root_path, db_path_replaced)

    connection = await aiosqlite.connect(db_path)
    db_wrapper = DBWrapper(connection)
    coin_store = await CoinStore.create(db_wrapper)

    keychain = Keychain()
    all_sks = keychain.get_all_private_keys()
    ph_pool_pk = {}

    for sk, _ in all_sks:
        pool_pk = str(master_sk_to_pool_sk(sk).get_g1());
        puzzle_hashes = []
        for i in range(500):
            ph = create_puzzlehash_for_pk(master_sk_to_wallet_sk(sk, uint32(i)).get_g1())
            puzzle_hashes.append(ph)
            ph_pool_pk[ph.hex()] = pool_pk

    coins = await coin_store.get_coin_records_by_puzzle_hashes(puzzle_hashes=puzzle_hashes, include_spent_coins=True)
    await connection.close()

    summary = {}

    for coin in coins:
        key = ph_pool_pk[coin.coin.puzzle_hash.hex()]
        balance = 0
        rewards = 0

        if coin.spent == False:
            try:
                balance = summary[key]['balance']
                balance = balance + coin.coin.amount
            except KeyError:
                balance = coin.coin.amount

            if coin.coinbase == True:
                try:
                    rewards = summary[key]['rewards']
                    rewards = rewards + coin.coin.amount
                except KeyError:
                    rewards = coin.coin.amount
        else:
            if coin.coinbase == True:
                try:
                    rewards = summary[key]['rewards']
                    rewards = rewards + coin.coin.amount
                except KeyError:
                    rewards =  coin.coin.amount

        if balance == 0:
            try:
                balance = summary[key]['balance']
            except KeyError:
                balance = 0

        if rewards == 0:
            try:
                rewards = summary[key]['rewards']
            except KeyError:
                rewards = 0

        summary[key] = {'balance': balance, 'rewards': rewards}

    for s in summary:
        print("Spendable balance:", float(summary[s]['balance']) / 10 ** 12, f"pool pk: {s}")
        print("Total farming rewards:", float(summary[s]['rewards']) / 10 ** 12, f"pool pk: {s}")
