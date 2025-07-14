import requests
import os
import logging

# API endpoint - use environment variable or default
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("dash_api")

def check_connection_status():
    """Check if the backend is connected to Interactive Brokers"""
    try:
        response = requests.get(f"{BACKEND_URL}/status", timeout=5)
        if response.status_code == 200:
            return response.json().get("connected", False)
        return False
    except Exception as e:
        logger.error(f"Error checking connection status: {str(e)}")
        return False

def place_order(order_details):
    """Place an order with the backend API"""
    try:
        response = requests.post(f"{BACKEND_URL}/order", json=order_details)
        return response.json()
    except Exception as e:
        return {"success": False, "message": f"Error communicating with backend: {str(e)}"}

def get_stock_info(ticker):
    """Get stock information from the backend API"""
    try:
        # For company name, we'll use a simple approach - in a real app, you might want to use a more robust API
        # This is a simplified example - you might want to use a more comprehensive API for company information
        company_name = get_company_name(ticker)
        
        return {
            'ticker': ticker,
            'name': company_name,
        }
    except Exception as e:
        logger.error(f"Error getting stock info for {ticker}: {str(e)}")
        return None

def get_company_name(ticker):
    """Get company name for a ticker using the backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/company_name/{ticker}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("company_name", ticker)
        else:
            logger.warning(f"Failed to get company name for {ticker}: {response.status_code}")
            return ''
    except Exception as e:
        logger.error(f"Error fetching company name for {ticker}: {str(e)}")
        return ''

def get_real_time_prices(tickers):
    """Get real-time prices for multiple tickers"""
    try:
        if not tickers:
            return {}
            
        response = requests.post(f"{BACKEND_URL}/prices", json={"symbols": tickers})
        
        if response.status_code != 200:
            logger.error(f"Error fetching prices: {response.text}")
            return {}
        
        data = response.json()
        
        if "error" in data:
            logger.error(f"API error: {data['error']}")
            return {}
        
        return data.get("prices", {})
    except Exception as e:
        logger.error(f"Error getting real-time prices: {str(e)}")
        return {}
