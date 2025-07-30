import time
from web3 import Web3
from collections import defaultdict
from .config import WEB3_PROVIDER, WATCHED_ADDRESSES, BIG_TX_THRESHOLD_ETH, TX_PER_MINUTE_THRESHOLD
from .utils import wei_to_eth

class BlockWatchdog:
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
        assert self.web3.is_connected(), "Web3 provider connection failed."
        self.address_activity = defaultdict(list)

    def monitor(self):
        print("[*] Starting block monitoring...")
        latest_block = self.web3.eth.block_number

        while True:
            current_block = self.web3.eth.block_number
            if current_block > latest_block:
                for blk_num in range(latest_block + 1, current_block + 1):
                    block = self.web3.eth.get_block(blk_num, full_transactions=True)
                    self.analyze_block(block)
                latest_block = current_block
            time.sleep(2)

    def analyze_block(self, block):
        print(f"[+] Block #{block.number} | Tx count: {len(block.transactions)}")
        for tx in block.transactions:
            self.analyze_transaction(tx)

    def analyze_transaction(self, tx):
        from_addr = tx["from"]
        to_addr = tx["to"]
        value_eth = wei_to_eth(tx["value"])

        now = time.time()
        self.address_activity[from_addr].append(now)
        self.address_activity[from_addr] = [t for t in self.address_activity[from_addr] if now - t < 60]

        if len(self.address_activity[from_addr]) > TX_PER_MINUTE_THRESHOLD:
            print(f"[!] HIGH ACTIVITY: {from_addr} sent {len(self.address_activity[from_addr])} txs in 1 minute.")

        if value_eth > BIG_TX_THRESHOLD_ETH:
            print(f"[!] BIG TRANSFER: {value_eth} ETH from {from_addr} to {to_addr}")

        if to_addr in WATCHED_ADDRESSES.values() or from_addr in WATCHED_ADDRESSES.values():
            label = next((k for k, v in WATCHED_ADDRESSES.items() if v in (from_addr, to_addr)), "Unknown")
            print(f"[!] WATCHED ADDRESS ACTIVITY ({label}): {from_addr} -> {to_addr} | {value_eth} ETH")
