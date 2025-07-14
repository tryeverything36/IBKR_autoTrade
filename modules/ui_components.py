import streamlit as st

def create_sidebar(config):
    """Create sidebar with connection settings"""
    st.sidebar.header("Connection Settings")
    
    host = st.sidebar.text_input(
        "Host", 
        value=config["ibkr"]["host"],
        help="IBKR TWS/Gateway host address"
    )
    
    port = st.sidebar.number_input(
        "Port", 
        value=config["ibkr"]["port"],
        help="7497 for TWS paper trading, 7496 for TWS live, 4002 for Gateway"
    )
    
    client_id = st.sidebar.number_input(
        "Client ID", 
        value=config["ibkr"]["client_id"],
        help="Unique client ID for this connection"
    )
    
    return {
        "host": host,
        "port": port,
        "client_id": client_id
    }

def create_order_form():
    """Create order form UI"""
    st.header("Place Order")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Define a list of common stock symbols
        stock_symbols = ["MSFT", "AAPL", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", "INTC", "JPM"]
        
        # Create a dropdown for symbol selection with option to enter custom symbol
        symbol_option = st.selectbox(
            "Symbol",
            options=["Select from list...", "Enter custom..."] + stock_symbols,
            index=0,
            help="Stock ticker symbol"
        )
        
        # Handle custom symbol entry
        if symbol_option == "Enter custom...":
            symbol = st.text_input("Enter symbol", value="", help="Enter stock ticker symbol")
        elif symbol_option == "Select from list...":
            symbol = ""  # Default empty if nothing selected yet
        else:
            symbol = symbol_option
            
        action = st.radio("Action", options=["buy", "sell"])
        quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
    
    with col2:
        limit_price = st.number_input(
            "Limit Price ($)", 
            min_value=0.01, 
            value=439.6,
            step=0.01,
            format="%.2f"
        )
        
        trailing_stop_enabled = st.checkbox("Enable Trailing Stop", value=True)
        
        trailing_stop_percentage = st.number_input(
            "Trailing Stop (%)", 
            min_value=0.1, 
            max_value=20.0, 
            value=2.0, 
            step=0.1,
            format="%.1f",
            disabled=not trailing_stop_enabled
        )
    
    return {
        "symbol": symbol,
        "action": action,
        "quantity": quantity,
        "limit_price": limit_price,
        "trailing_stop_enabled": trailing_stop_enabled,
        "trailing_stop_percentage": trailing_stop_percentage
    }