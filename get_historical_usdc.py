'''
A script for finding your polygon wallet address's USDC balance historically
 - Start with a block you would like to begin with, corresponding to a date you're
    interested in. You can grab this from a block explorer like Polyscan
 - Enter your Polygon Address, and a number of days
 - Saves the output to CSV for further analysis
'''

import time
import pandas as pd
from web3 import Web3
from datetime import datetime, timezone
from web3.middleware import geth_poa_middleware


def connect_to_polygon() -> Web3:
    # Replace with your actual endpoint
    polygon_rpc_url = "https://polygon-rpc.com" 
    
    web3 = Web3(Web3.HTTPProvider(polygon_rpc_url))

    # Inject the PoA middleware to handle extraData length
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not web3.is_connected():
        raise ConnectionError("Failed to connect to the Polygon network")

    return web3


def get_block_timestamp(block_number: int) -> int:
    # Assuming you have a Web3 instance connected to a node
    web3 = connect_to_polygon()

    # Fetch the block information using its number
    block = web3.eth.get_block(block_number)

    # Extract the timestamp
    timestamp = block['timestamp']

    # Convert the timestamp to a human-readable format if needed
    readable_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    print(f"Timestamp for block {block_number}: {readable_timestamp} UTC")

    return readable_timestamp, timestamp


def get_wallet_balance(user_address: str, block_number: int = 'latest') -> float:
    
    web3 = connect_to_polygon()

    # USDC contract address on Polygon
    usdc_contract_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

    # ABI for ERC-20 token balanceOf function
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        }
    ]

    # Create a contract object
    usdc_contract = web3.eth.contract(address=usdc_contract_address, abi=erc20_abi)

    # Get the balance of USDC for the wallet at the specific block
    balance_wei = usdc_contract.functions.balanceOf(user_address).call(block_identifier=block_number)

    # Convert the balance to the appropriate decimal (USDC has 6 decimals)
    balance_usdc = balance_wei / 10**6

    print(f"USDC Balance for wallet {user_address} at block {block_number}: {balance_usdc} USDC")

    return balance_usdc


def print_block_info(user_address, blocks_per_day, start_block, num_days):
    current_block = start_block

    for day in range(num_days):
        # Get block timestamp and wallet balance
        get_block_timestamp(current_block)
        get_wallet_balance(user_address, current_block)

        print()
        
        # Move to the next block after 24 hours
        current_block += blocks_per_day


def calculate_average_block_time(num_blocks: int = 100) -> float:

    web3 = connect_to_polygon()
    latest_block = web3.eth.block_number
    timestamps = []
    
    for i in range(num_blocks):
        block_number = latest_block - i
        timestamp = get_block_timestamp(block_number)[1]
        timestamps.append(timestamp)
        time.sleep(.25)
    
    # Calculate differences between consecutive timestamps
    time_differences = [timestamps[i] - timestamps[i + 1] for i in range(len(timestamps) - 1)]
    
    # Calculate the average block time
    average_block_time = sum(time_differences) / len(time_differences)
    
    return average_block_time


def blocks_per_day() -> int:

    seconds_per_day = 60 * 60 * 24
    # print(seconds_per_day)

    avg_block_time = calculate_average_block_time(20)

    blocks_per_day = seconds_per_day / avg_block_time
    blocks_per_day = int(blocks_per_day)

    return blocks_per_day


def print_and_save_block_info(user_address: str, blocks_per_day: int, start_block: int, num_days: int, output_csv_file: str) -> None:

    current_block = start_block

    # List to store data
    data = []

    for day in range(num_days):
        # Get block timestamp and wallet balance
        timestamp, _ = get_block_timestamp(current_block)
        usdc_balance = get_wallet_balance(user_address, current_block)

        # Print to console
        print(f"Timestamp for block {current_block}: {timestamp}")
        print(f"USDC Balance for wallet {user_address} at block {current_block}: {usdc_balance} USDC")
        print()

        # Append data to the list
        data.append({
            'Block': current_block,
            'Timestamp': timestamp,
            'USDC Balance': usdc_balance
        })
        
        # Move to the next block after 24 hours
        current_block += blocks_per_day

        # sleeping helped keep the connection to Polygon alive for some reason
        time.sleep(1)

    # Convert list to DataFrame
    df = pd.DataFrame(data)

    # Save to CSV
    df.to_csv(output_csv_file, index=False)



# Example usage 
user_address = "0x7C3Db723F1D4d8cB9C550095203b686cB11E5C6B"
blocks_24 = blocks_per_day()
start_block = 53293320
num_days = 5  # Number of days to retrieve
output_csv_file = 'usdc_balance_over_time.csv'


if __name__ == "__main__":
    print_and_save_block_info(user_address, blocks_24, start_block, num_days, output_csv_file)