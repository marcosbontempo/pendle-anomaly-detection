import os
import time
from web3 import Web3
from dotenv import load_dotenv, find_dotenv

# Load RPC from .env
load_dotenv(find_dotenv("../.env"))
RPC_URL = os.getenv("RPC_URL")
web3 = Web3(Web3.HTTPProvider(RPC_URL))

PENDLE_CONTRACT_ADDRESS = "0x0c880f6761F1af8d9Aa9C466984b80DAb9a8c9e8"

# Start monitoring from the latest block
latest_block = web3.eth.block_number

print("📡 Monitoring Pendle transactions...")

while True:
    try:
        current_block = web3.eth.block_number  # Get the latest block number
        
        # If no new blocks, wait and retry
        if current_block <= latest_block:
            time.sleep(5)
            continue

        print(f"🔄 Checking transactions from block {latest_block} to {current_block}")

        logs = web3.eth.get_logs({
            "fromBlock": latest_block,
            "toBlock": current_block,
            "address": PENDLE_CONTRACT_ADDRESS
        })

        if logs:
            print(f"🔎 Found {len(logs)} new logs")
            for log in logs:
                print(log)  # Print each transaction

        latest_block = current_block + 1  # Move to the next block

    except Exception as e:
        print(f"⚠️ Error fetching logs: {e}")
        time.sleep(10)  # Wait before retrying in case of an error
