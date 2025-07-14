import pandas as pd
import random
from datetime import datetime
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("data_utils")

# Define the path for the data file
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"))
DATA_FILE = os.path.join(DATA_DIR, "stock_data.json")

def create_dataframe(data_dict):
    """Create a DataFrame from the table data dictionary"""
    rows = []
    for name, details in data_dict.items():
        row = {
            "Name": name,
            "Ticker": details["ticker"],
            "Price": float(details["price"]) if details["price"] else 0,
            "Number": int(details["number"]) if details["number"] else 0,
        }
        
        # Calculate the Total as the total P&L
        if "total_pnl" in details and details["total_pnl"]:
            row["Total"] = float(details["total_pnl"])
        else:
            row["Total"] = 0
            
        # Add additional fields if they exist
        if "opening_price" in details and details["opening_price"]:
            row["Opening_Price"] = details["opening_price"]
            
        if "closing_price" in details and details["closing_price"]:
            row["Closing_Price"] = details["closing_price"]
            
        if "pnl" in details and details["pnl"]:
            row["PnL"] = float(details["pnl"])
            
        rows.append(row)
        
    return pd.DataFrame(rows)

def get_real_time_price(ticker, current_price=None):
    """Get real-time price for a ticker - this is a placeholder"""
    # In a real app, this would call an API to get the current price
    # For now, we'll just simulate price changes
    if current_price is None:
        return 0
    else:
        return current_price


def save_table_data(data_dict):
    """Save the table data to a JSON file"""
    try:
        # Ensure the data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)

        # Save the data to a JSON file
        with open(DATA_FILE, 'w') as f:
            json.dump(data_dict, f)

        logger.info(f"Table data saved to {DATA_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving table data: {str(e)}")
        return False

def load_table_data():
    """Load the table data from a JSON file"""
    try:
        # Check if the file exists
        if not os.path.exists(DATA_FILE):
            logger.info(f"No saved data found at {DATA_FILE}")
            return {}

        # Load the data from the JSON file
        with open(DATA_FILE, 'r') as f:
            data_dict = json.load(f)

        logger.info(f"Table data loaded from {DATA_FILE}")
        return data_dict
    except Exception as e:
        logger.error(f"Error loading table data: {str(e)}")
        return {}
