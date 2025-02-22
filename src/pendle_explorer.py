import os
import json
from dotenv import load_dotenv, find_dotenv
from web3 import Web3

# Load .env from the parent directory
load_dotenv(find_dotenv("../.env"))

RPC_URL = os.getenv("RPC_URL")
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("❌ Failed to connect to RPC Node!")
    exit()

print("✅ Connected to Ethereum/Arbitrum RPC!")

PENDLE_CONTRACT_ADDRESS = "0x0c880f6761F1af8d9Aa9C466984b80DAb9a8c9e8"

# Correct ERC-20 Transfer event ABI
ABI = json.loads("""
[
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]
""")

pendle_contract = web3.eth.contract(address=PENDLE_CONTRACT_ADDRESS, abi=ABI)

def handle_event(event):
    tx_hash = event["transactionHash"].hex()
    from_address = event["args"]["from"]
    to_address = event["args"]["to"]
    amount = web3.from_wei(event["args"]["value"], "ether")

    print(f"🚀 New Pendle Transaction 🚀")
    print(f"🔹 From: {from_address}")
    print(f"🔹 To: {to_address}")
    print(f"🔹 Amount: {amount} PENDLE")
    print(f"🔹 TX Hash: {tx_hash}")
    print("-" * 50)

print("📡 Monitoring Pendle transactions...")

latest_block = web3.eth.block_number

while True:
    try:
        logs = web3.eth.get_logs({
            "fromBlock": latest_block,
            "toBlock": "latest",
            "address": PENDLE_CONTRACT_ADDRESS
        })
        
        for log in logs:
            print(f"🔎 Raw Event Log: {log}")  # Print full log to debug

            if log["topics"]:
                event_signature_received = log["topics"][0].hex()
                print(f"📜 Received Event Signature: {event_signature_received}")

            try:
                event_data = pendle_contract.events.Transfer().process_log(log)
                handle_event(event_data)
            except Exception as e:
                print(f"⚠️ Error processing log: {e}")

        latest_block = web3.eth.block_number

    except Exception as e:
        print(f"⚠️ Error fetching logs: {e}")

