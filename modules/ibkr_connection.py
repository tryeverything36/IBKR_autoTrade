from ib_insync import IB, util
import logging
import asyncio
import nest_asyncio
import streamlit as st
import time

from modules.order_manager import OrderManager

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

class IBKRConnection:
    def __init__(self, host="127.0.0.1", port=7497, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.order_manager = None
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def on_order_filled(self, trade):
        if trade.orderStatus.status == 'Filled' and trade.order.action == 'BUY':
            self.order_manager.start_trailing_stop_monitor(
                trade.contract.symbol
            )
            self.logger.info(
                f"Buy order filled at {trade.fills[-1].execution.price if trade.fills else 'unknown'} price. Trailing stop activated.")

    def connect(self):
        """Connect to Interactive Brokers"""
        try:
            if not self.ib.isConnected():
                self.ib.connect(self.host, self.port, clientId=self.client_id)
                
                # Wait for connection to establish
                time.sleep(1)
                
                if self.ib.isConnected():
                    self.logger.info(f"Connected to IBKR at {self.host}:{self.port}")
                    
                    # Import here to avoid circular imports
                    from modules.order_manager import OrderManager
                    self.order_manager = OrderManager(self.ib)
                    
                    # Set up callbacks
                    self.ib.orderStatusEvent += self.on_order_filled
                    
                    return True
                else:
                    self.logger.error("Failed to connect to IBKR")
                    return False
            else:
                self.logger.info("Already connected to IBKR")
                return True
        except Exception as e:
            self.logger.error(f"Error connecting to IBKR: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.ib.isConnected():
            self.ib.disconnect()
            self.logger.info("Disconnected from IBKR")

    def is_connected(self):
        """Check if connected to Interactive Brokers"""
        if not self.ib.isConnected():
            return self.connect()
        return self.ib.isConnected()

    def get_ib(self):
        """Get the IB instance"""
        return self.ib
