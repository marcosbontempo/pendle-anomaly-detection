import os
import json
import time
import requests
from web3 import Web3
from dotenv import load_dotenv, find_dotenv

# Load .env from the parent directory
load_dotenv(find_dotenv("../.env"))

RPC_URL = os.getenv("RPC_URL")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")  
CEX_WALLETS_FILE = "known_cex_wallets.json"

web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("❌ Failed to connect to RPC Node!")
    exit()

print("✅ Connected to Ethereum/Arbitrum RPC!")

PENDLE_CONTRACT_ADDRESS = "0x0c880f6761F1af8d9Aa9C466984b80DAb9a8c9e8"
TRANSFER_EVENT_SIGNATURE = Web3.keccak(text="Transfer(address,address,uint256)").hex()

latest_block = web3.eth.block_number  # Start from the latest block

# Load or create known CEX wallets file
if os.path.exists(CEX_WALLETS_FILE):
    with open(CEX_WALLETS_FILE, "r") as file:
        known_cex_wallets = json.load(file)
else:
    known_cex_wallets = {}

# ✅ Check if an address is a contract (DEX)
def is_contract(address):
    code = web3.eth.get_code(Web3.to_checksum_address(address))
    return code != b''  # True if it's a smart contract (DEX)

# ✅ Check if an address is a CEX wallet (cached + Etherscan API)
def is_cex_wallet(address):
    address = Web3.to_checksum_address(address)

    if address in known_cex_wallets:
        return known_cex_wallets[address]

    # Query Etherscan API to check if it's an exchange
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&apikey={ETHERSCAN_API_KEY}"
    try:
        response = requests.get(url).json()
        if response.get("status") == "1" and response.get("result"):
            for tx in response["result"][:5]:  
                if any(exchange in tx.get("to", "").lower() or exchange in tx.get("from", "").lower() 
                       for exchange in ["binance", "coinbase", "okx"]):
                    known_cex_wallets[address] = True  
                    with open(CEX_WALLETS_FILE, "w") as file:
                        json.dump(known_cex_wallets, file)
                    return True  

    except Exception as e:
        print(f"⚠️ Failed to check CEX wallet: {e}")

    known_cex_wallets[address] = False
    with open(CEX_WALLETS_FILE, "w") as file:
        json.dump(known_cex_wallets, file)
    
    return False

# ✅ Classify transaction type
def classify_transaction(from_address, to_address):
    from_contract = is_contract(from_address)
    to_contract = is_contract(to_address)

    if is_cex_wallet(from_address):
        return "CEX", "withdraw"
    elif is_cex_wallet(to_address):
        return "CEX", "deposit"
    elif from_contract or to_contract:
        return "DEX", "buy" if from_contract else "sell"
    else:
        return "wallet-to-wallet", None

print("📡 Monitoring Pendle transactions...")

while True:
    try:
        current_block = web3.eth.block_number  # Get the latest block number

        if current_block <= latest_block:
            time.sleep(5)
            continue

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

                        # ✅ Classify transaction
                        operation_type, direction = classify_transaction(from_address, to_address)

                        print(f"  - From: {from_address}")
                        print(f"  - To: {to_address}")
                        print(f"  - Value: {amount_pendle} PENDLE")
                        print(f"  - Type: {operation_type}")
                        print(f"  - Direction: {direction if direction else 'N/A'}")
                        print("-" * 50)

                except Exception as e:
                    print(f"⚠️ Error processing log: {e}")

        latest_block = current_block + 1  # Move to the next block

        time.sleep(5)  # Avoid overloading RPC

    except Exception as e:
        print(f"⚠️ Error fetching logs: {e}")
        time.sleep(10)  
