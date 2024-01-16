import requests
import csv
from datetime import datetime
from bs4 import BeautifulSoup

# Function to get the 'Mid' value from the website in pounds
def get_stock_value():
    url = "https://www.aquis.eu/companies/KR1?securityidaqse=KR1"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            divs = soup.find_all('div', class_='css-s2uf1z')
            for div in divs:
                p_tags = div.find_all('p', class_='chakra-text css-dro5jl')
                for p in p_tags:
                    if p.text.strip() == 'Mid':
                        mid_value_pence = div.find('p', class_='chakra-text css-4vttjp').text.strip()
                        mid_value_pounds = float(mid_value_pence) / 100
                        return mid_value_pounds
        else:
            print("Failed to retrieve the 'Mid' value from the website. Status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the 'Mid' value: {e}")
    
    # If the function has not returned by this point, ask the user for input
    try:
        return float(input("Unable to retrieve the 'Mid' value. Please enter the current share value in pounds: "))
    except ValueError:
        print("Invalid input. Please ensure you enter a numeric value.")
        return None

current_share_value = get_stock_value()

def append_to_csv(pb_ratio, current_share_value, total_holdings_gbp, market_cap, usd_to_gbp_exchange_rate):
    # Get the current date and time
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')
    
    # Data to be appended, manually formatting as a quoted string
    data = [f'"{current_date}"', f'"{current_time}"', f'"{pb_ratio}"', f'"{current_share_value}"', f'"{total_holdings_gbp}"', f'"{market_cap}"', f'"{usd_to_gbp_exchange_rate}"']

    # Append data to the CSV file
    with open('results.csv', mode='a', newline='') as file:
        file.write(','.join(data) + '\n')

# Function to get the current USD to GBP exchange rate
def get_usd_to_gbp_exchange_rate():
    url = "https://api.exchangerate-api.com/v4/latest/USD"  # Replace with your chosen API endpoint
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['rates']['GBP']
        else:
            return None
    except requests.exceptions.RequestException:
        return None

# Function to get the prices of cryptocurrencies in USD using the CoinGecko API
def get_crypto_prices(ids):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ','.join(ids),
        'vs_currencies': 'usd',
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None

# Attempt to fetch the USD to GBP exchange rate
usd_to_gbp_exchange_rate = get_usd_to_gbp_exchange_rate()

if usd_to_gbp_exchange_rate is None:
    print("Failed to retrieve USD to GBP exchange rate.")
    exit()

# Updated dictionary mapping cryptocurrency IDs to the number of tokens
tokens_per_crypto = {
    "lido-dao": 15000000,
    "polkadot": 3965940,
    "cosmos": 1372687,
    "staked-ether": 4639,
    "celestia": 7500000,
    "rocket-pool": 256000,
    "moonbeam": 13921874,
    "nxm": 110680,
    "astar": 52874796 
}

# Exchange rate from USD to GBP
#usd_to_gbp_exchange_rate = 0.7978936

# List of cryptocurrency IDs to fetch prices for
crypto_ids = list(tokens_per_crypto.keys())

# Call the function to get prices
crypto_prices = get_crypto_prices(crypto_ids)

# Total number of shares
total_shares = 177369520
market_cap = total_shares * current_share_value

# Initialise total holdings in GBP
total_holdings_gbp = 0

# Dictionary to store the GBP value for each cryptocurrency
holdings_gbp = {}

# Calculate the total value in GBP per cryptocurrency
if crypto_prices is not None:
    for crypto_id, num_tokens in tokens_per_crypto.items():
        if crypto_id in crypto_prices and 'usd' in crypto_prices[crypto_id]:
            price_usd = crypto_prices[crypto_id]['usd']
            total_value_usd = price_usd * num_tokens
            total_value_gbp = total_value_usd * usd_to_gbp_exchange_rate
            holdings_gbp[crypto_id] = total_value_gbp
            total_holdings_gbp += total_value_gbp
        else:
            print(f"Price for {crypto_id} not found.")
else:
    print("Could not retrieve the cryptocurrency prices.")

# Add hardcoded values for Zee Prime II and Subspace Labs Inc
holdings_gbp["Zee Prime II"] = 5443347
holdings_gbp["Subspace Labs Inc"] = 1168975

# Update the total holdings with the hardcoded values
total_holdings_gbp += holdings_gbp["Zee Prime II"] + holdings_gbp["Subspace Labs Inc"]

# Calculate the Net Asset Value (NAV) per share in GBP
nav_per_share_gbp = total_holdings_gbp / total_shares if total_shares > 0 else 0

# Sort the holdings by value in descending order
sorted_holdings_gbp = dict(sorted(holdings_gbp.items(), key=lambda item: item[1], reverse=True))

# price-to-book (P/B) ratio
# pb_ratio = total_holdings_gbp / (total_shares * current_share_value) if total_shares > 0 else 0
pb_ratio = current_share_value / nav_per_share_gbp

# Print the sorted total holdings
for crypto_id, value_gbp in sorted_holdings_gbp.items():
    #print(f"Total GBP value for {tokens_per_crypto.get(crypto_id, 'N/A')} tokens of {crypto_id}: £{value_gbp:,.0f}")
    print(f"{crypto_id}: £{round(value_gbp / 1_000_000)}M")

print()

# Print the total holdings and NAV per share in GBP with commas and no decimals
print(f"Total asset holdings in GBP: £{total_holdings_gbp/1_000_000:.0f}M")
print(f"Market capitalization: £{market_cap/1_000_000:,.0f}M")

print(f"Current share price: £{current_share_value:,.2f}")
print(f"Net Asset Value (NAV) per share: £{nav_per_share_gbp:,.2f}")

# Print the P/B ratio
print(f"Price-to-Book (P/B) Ratio: {pb_ratio:.2f}")

append_to_csv(pb_ratio, current_share_value, total_holdings_gbp, market_cap, usd_to_gbp_exchange_rate)
