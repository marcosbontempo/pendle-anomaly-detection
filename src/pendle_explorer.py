import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv, find_dotenv

# Load .env from the parent directory
load_dotenv(find_dotenv("../.env"))

RPC_URL = os.getenv("RPC_URL")
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("❌ Failed to connect to RPC Node!")
    exit()

print("✅ Connected to Ethereum/Arbitrum RPC!")

PENDLE_CONTRACT_ADDRESS = "0x0c880f6761F1af8d9Aa9C466984b80DAb9a8c9e8"
TRANSFER_EVENT_SIGNATURE = Web3.keccak(text="Transfer(address,address,uint256)").hex()  # Gerar hash correto

latest_block = web3.eth.block_number  # Start from the latest block

print("📡 Monitoring Pendle transactions...")

while True:
    try:
        current_block = web3.eth.block_number  # Get the latest block number

        if current_block <= latest_block:
            time.sleep(5)
            continue

        #print(f"🔄 Checking transactions from block {latest_block} to {current_block}")

        logs = web3.eth.get_logs({
            "fromBlock": latest_block,
            "toBlock": current_block,
            "address": PENDLE_CONTRACT_ADDRESS
        })

        if logs:
            for log in logs:
                try:
                    event_signature_received = log["topics"][0].hex()

                    if event_signature_received.lower() == TRANSFER_EVENT_SIGNATURE.lower():
                        from_address = "0x" + log["topics"][1].hex()[-40:]
                        to_address = "0x" + log["topics"][2].hex()[-40:]

                        amount = int(log["data"].hex(), 16)  # Convert from Hex to int
                        amount_pendle = web3.from_wei(amount, "ether")  # Converter para unidades corretas

                        print(f"✅ New Transfer Event:")
                        print(f"  - From: {from_address}")
                        print(f"  - To: {to_address}")
                        print(f"  - Value: {amount_pendle} PENDLE")
                        print("-" * 50)

                    #else:
                    #    print(f"⚠️ Unknown Event Signature: {event_signature_received}")
                    #    print(f"🔎 RAW LOG DATA: {log}")

                except Exception as e:
                    print(f"⚠️ Error processing log: {e}")
                    print(f"🔍 RAW LOG: {log}")  # Print raw log for debugging

        #else:
        #    print("⚠️ No new transactions found.")

        latest_block = current_block + 1  # Move to the next block

        time.sleep(5)  # Avoid overloading RPC

    except Exception as e:
        print(f"⚠️ Error fetching logs: {e}")
        time.sleep(10)  
