from ib_insync import Stock, LimitOrder, OrderStatus
import threading
import time
import logging

class OrderManager:
    def __init__(self, ib):
        self.ib = ib
        self.stop_monitors = {}
        self.logger = logging.getLogger(__name__)
        self.symbol_data = {}
    
    def place_order(self, order_details):
        """Place a limit order"""
        try:
            self.symbol_data[order_details["symbol"]] = order_details
            # Create contract
            contract = Stock(order_details["symbol"], "SMART", "USD")

            # Create order
            action = "BUY" if order_details["action"] == "buy" else "SELL"
            limit_order = LimitOrder(
                action=action,
                totalQuantity=order_details["quantity"],
                lmtPrice=order_details["limit_price"],
                outsideRth=True  # Allow trading outside regular trading hours
            )
            
            # Submit order
            trade = self.ib.placeOrder(contract, limit_order)
            self.ib.sleep(1)  # Give time for order to be processed

            return {
                "success": True,
                "message": f"Order placed: {order_details['symbol']} {action} {order_details['quantity']} shares at ${order_details['limit_price']}",
                "trade": trade
            }
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def start_trailing_stop_monitor(self, symbol):
        """Start monitoring for trailing stop"""
        if symbol in self.stop_monitors:
            # Stop existing monitor if any
            self.stop_monitors[symbol]["running"] = False

        order_details = self.symbol_data.get(symbol)
        trail_stop_percentage = order_details.get("trailing_stop_percentage", 0)

        # Create new monitor thread
        monitor_thread = threading.Thread(
            target=self._trailing_stop_monitor,
            args=(symbol, trail_stop_percentage),
            daemon=True
        )
        
        self.stop_monitors[symbol] = {
            "thread": monitor_thread,
            "running": True,
            "stop_percentage": trail_stop_percentage,
            "highest_price": 0
        }
        
        monitor_thread.start()
        self.logger.info(f"Started trailing stop monitor for {symbol} with {trail_stop_percentage}% stop")
    
    def _trailing_stop_monitor(self, symbol, stop_percentage):
        """Monitor price and execute trailing stop"""
        contract = Stock(symbol, "SMART", "USD")
        monitor_data = self.stop_monitors[symbol]
        order_details = self.symbol_data.get(symbol)

        while monitor_data["running"]:
            try:
                # Get current market price
                self.ib.reqMarketDataType(1)  # 1 = Live data
                ticker = self.ib.reqMktData(contract)
                self.ib.sleep(2)  # Wait for data
                
                current_price = ticker.marketPrice()
                
                if current_price > 0:
                    # Update highest price if current price is higher
                    if current_price > monitor_data["highest_price"]:
                        monitor_data["highest_price"] = current_price
                        self.logger.info(f"Updated highest price for ts order of {symbol} to {monitor_data['highest_price']}")
                    
                    # Calculate stop price
                    stop_price = monitor_data["highest_price"] * (1 - stop_percentage / 100)
                    
                    # Check if stop is triggered
                    if current_price <= stop_price and monitor_data["highest_price"] > 0:
                        self.logger.info(f"Trailing stop triggered for {symbol} at {current_price}")
                        
                        # Place sell order
                        sell_order = LimitOrder(
                            action="SELL",
                            totalQuantity=order_details['quantity'],
                            lmtPrice=current_price,
                            outsideRth=True
                        )
                        
                        trade = self.ib.placeOrder(contract, sell_order)
                        self.logger.info(f"Placed sell order for {symbol} at {current_price}")
                        
                        # Stop monitoring
                        monitor_data["running"] = False
                        break
                
                time.sleep(10)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in trailing stop monitor: {str(e)}")
                time.sleep(30)  # Wait before retrying
        
        self.logger.info(f"Stopped trailing stop monitor for {symbol}")
