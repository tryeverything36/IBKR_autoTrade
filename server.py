import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import nest_asyncio
import logging
from ib_insync import Stock

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ibkr_backend")

from modules.config import load_config

# Create FastAPI app
app = FastAPI(title="IBKR Backend API")

# Global connection and order manager
ibkr_connection = None
order_manager = None

# Models
class OrderDetails(BaseModel):
    symbol: str
    action: str
    quantity: int
    limit_price: float
    trailing_stop_enabled: bool
    trailing_stop_percentage: float

class OrderResponse(BaseModel):
    success: bool
    message: str
    order_id: Optional[str] = None

# New model for price requests
class PriceRequest(BaseModel):
    symbols: List[str]

@app.on_event("startup")
async def startup_event():
    """Connect to IBKR automatically on server startup"""
    # Load configuration on startup
    config = load_config()
    
    # Initialize connection with default parameters
    await initialize_connection(
        host=config["ibkr"]["host"],
        port=config["ibkr"]["port"],
        client_id=config["ibkr"]["client_id"]
    )

async def initialize_connection(host, port, client_id):
    """Initialize connection to IBKR"""
    global ibkr_connection
    
    try:
        # Import here to avoid circular imports
        from modules.ibkr_connection import IBKRConnection
        
        ibkr_connection = IBKRConnection(host=host, port=port, client_id=client_id)
        connected = ibkr_connection.connect()
        
        if connected:
            logger.info(f"Connected to IBKR at {host}:{port} with client ID {client_id}")
            return True
        else:
            logger.error("Failed to connect to IBKR")
            return False
    except Exception as e:
        logger.error(f"Error connecting to IBKR: {str(e)}")
        return False

@app.get("/status")
async def get_status():
    """Get connection status"""
    if ibkr_connection and ibkr_connection.is_connected():
        return {"connected": True}
    return {"connected": False}

@app.post("/order", response_model=OrderResponse)
async def place_order(order: OrderDetails):
    """Place an order"""
    if not ibkr_connection or not ibkr_connection.is_connected():
        # Try to reconnect if not connected
        config = load_config()
        await initialize_connection(
            host=config["ibkr"]["host"],
            port=config["ibkr"]["port"],
            client_id=config["ibkr"]["client_id"]
        )
        
        if not ibkr_connection or not ibkr_connection.is_connected():
            raise HTTPException(status_code=400, detail="Not connected to IBKR and reconnection failed")
    
    if not ibkr_connection.order_manager:
        raise HTTPException(status_code=500, detail="Order manager not initialized")
    
    try:
        result = ibkr_connection.order_manager.place_order(order.dict())
        return result
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return {"success": False, "message": f"Error placing order: {str(e)}"}

@app.post("/prices")
async def get_prices(price_request: PriceRequest):
    """Get real-time prices for a list of symbols"""
    if not ibkr_connection or not ibkr_connection.is_connected():
        return JSONResponse(
            status_code=400,
            content={"error": "Not connected to Interactive Brokers"}
        )
    
    try:
        prices = {}
        ib = ibkr_connection.get_ib()
        
        for symbol in price_request.symbols:
            try:
                # Create contract
                contract = Stock(symbol, "SMART", "USD")
                
                # Qualify the contract
                qualified_contracts = ib.qualifyContracts(contract)
                if not qualified_contracts:
                    logger.warning(f"Could not qualify contract for {symbol}")
                    continue
                
                contract = qualified_contracts[0]
                
                # Request market data
                ib.reqMarketDataType(1)  # 1 = Live data
                ticker = ib.reqMktData(contract)
                
                # Wait briefly for data to arrive
                await asyncio.sleep(0.5)
                
                # Get the price
                price = ticker.marketPrice()
                if price > 0:
                    prices[symbol] = round(price, 2)
                else:
                    # Fallback to last price if market price is not available
                    price = ticker.last
                    if price > 0:
                        prices[symbol] = round(price, 2)
                    else:
                        # If no price is available, use the current price from the request
                        prices[symbol] = None
                
                # Cancel the market data subscription to avoid hitting limits
                ib.cancelMktData(contract)
                
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {str(e)}")
                prices[symbol] = None
        
        return {"prices": prices}
    except Exception as e:
        logger.error(f"Error fetching prices: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch prices: {str(e)}"}
        )

@app.get("/company_name/{ticker}")
async def get_company_name(ticker: str):
    """Get company name for a given ticker symbol"""
    try:
        if not ibkr_connection or not ibkr_connection.is_connected():
            # If not connected to IBKR, use a fallback method
            # This could be a simple dictionary for common stocks or another API
            logger.warning("Not connected to IBKR, using fallback method for company name")
            return {"company_name": ""}
        
        # Use IB API to get contract details which include company name
        ib = ibkr_connection.get_ib()
        contract = Stock(ticker, 'SMART', 'USD')
        
        # Request contract details
        details = ib.reqContractDetails(contract)
        
        if details and len(details) > 0:
            # The longName field contains the full company name
            company_name = details[0].longName
            return {"company_name": company_name}
        else:
            raise Exception(f"No contract details found for {ticker}")
    except Exception as e:
        logger.error(f"Error fetching company name: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch company name: {str(e)}"}
        )

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)