from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html
import plotly.graph_objects as go
from datetime import datetime
import math
import time

from ..utils.api import check_connection_status, place_order, get_stock_info, get_real_time_prices
from ..utils.data import create_dataframe, save_table_data, load_table_data

def register_callbacks(app):
    """Register all callbacks for the application"""
    
    # Add a client-side store for tracking when data changes
    # This will be used to trigger the save callback
    app.clientside_callback(
        """
        function(data) {
            return Date.now();
        }
        """,
        Output("data-change-timestamp", "data"),  # Using data property of dcc.Store
        Input("table-data-store", "data")
    )

    # Callback to save data when stock table changes
    @app.callback(
        Output("save-status", "data", allow_duplicate=True),  # Using data property of dcc.Store
        Input("stock-table", "data"),
        prevent_initial_call=True
    )
    def save_data_from_table(table_data):
        if not table_data:
            raise PreventUpdate

        # Convert table data to the format needed for storage
        table_data_store = {}
        for row in table_data:
            table_data_store[row["Name"]] = {
                "ticker": row["Ticker"],
                "price": str(row["Price"]) if "Price" in row and row["Price"] else "",
                "opening_price": str(row["Opening_Price"]) if "Opening_Price" in row and row["Opening_Price"] else "",
                "closing_price": str(row["Closing_Price"]) if "Closing_Price" in row and row["Closing_Price"] else "",
                "pnl": str(row["PnL"]) if "PnL" in row and row["PnL"] else "",
                "number": str(row["Number"]) if "Number" in row and row["Number"] else "0",
                "original_number": str(row.get("Original_Number", row.get("Number", "0"))),
                "total_pnl": str(row.get("Total", "0")),
                "shadow_pnl": str(row["Shadow_PnL"]) if "Shadow_PnL" in row and row["Shadow_PnL"] else ""
            }

        # Save the data to disk
        success = save_table_data(table_data_store)

        # Return status
        return {"success": success, "timestamp": time.time()}

    # Callback to update connection status
    @app.callback(
        Output("connection-status", "children"),
        Input("interval-component", "n_intervals")
    )
    def update_connection_status(n):
        is_connected = check_connection_status()
        if is_connected:
            return html.Div(
                dbc.Alert("Connected to Interactive Brokers", color="success"),
                className="mb-3"
            )
        else:
            return html.Div([
                dbc.Alert("Not connected to Interactive Brokers", color="danger"),
                dbc.Alert(
                    "Backend is not connected to Interactive Brokers. Please ensure the backend server is running properly.",
                    color="warning"
                )
            ], className="mb-3")

    # Callback to handle buy button click - work directly with the table data
    @app.callback(
        [Output("notification-area", "children"),
         Output("stock-table", "data", allow_duplicate=True)],
        [Input("buy-button", "n_clicks"),
         Input("sell-button", "n_clicks")],
        [State("stock-table", "selected_rows"),
         State("stock-table", "data"),
         State("order-amount-table", "data"),
         State("trailing-stop", "value")],
        prevent_initial_call=True
    )
    def handle_buy_sell_click(buy_clicks, sell_clicks, selected_rows, table_data, order_amount_data, trailing_stop):
        if not selected_rows or len(selected_rows) != 1:
            return dbc.Alert("Please select exactly one stock from the table", color="warning", dismissable=True), table_data

        selected_row = table_data[selected_rows[0]]
        ticker = selected_row["Ticker"]
        price = float(selected_row["Price"]) if selected_row["Price"] else 0

        # Find the corresponding row in the order amount table
        order_amount = 0
        for row in order_amount_data:
            if row["Ticker"] == ticker:
                try:
                    order_amount = float(row["Amount($)"])
                except (ValueError, TypeError):
                    order_amount = 0
                break

        # Calculate quantity based on dollar amount and current price
        quantity = 0
        if price > 0:
            quantity = math.floor(order_amount / price)  # Floor to ensure we don't exceed the dollar amount

        # Determine if buy or sell was clicked
        triggered_id = ctx.triggered_id
        action = "buy" if triggered_id == "buy-button" else "sell"

        # For sell orders, check if there are shares to sell
        if action == "sell":
            available_shares = int(selected_row.get("Number", 0))
            if available_shares <= 0:
                return dbc.Alert(f"No shares of {ticker} available to sell", color="warning", dismissable=True), table_data
            # For sell orders, use available shares if quantity is too high
            quantity = min(quantity, available_shares)

        # For buy orders, check if quantity is valid
        if action == "buy" and quantity <= 0:
            return dbc.Alert(f"Please set a valid dollar amount for {ticker} before placing an order", color="warning", dismissable=True), table_data

        # Prepare order details
        order_details = {
            "symbol": ticker,
            "action": action,
            "quantity": quantity,
            "limit_price": price,
            "trailing_stop_enabled": action == "buy",
            "trailing_stop_percentage": trailing_stop if action == "buy" else 0.0
        }

        # Place the order directly
        result = place_order(order_details)

        if result.get('success'):
            # Update the table data directly
            for i, row in enumerate(table_data):
                if row["Ticker"] == ticker:
                    if action == "buy":
                        # For buy orders, update opening price and quantity
                        table_data[i]["Opening_Price"] = price
                        table_data[i]["Number"] = quantity
                        # Store original position size for Shadow P&L calculation
                        table_data[i]["Original_Number"] = quantity
                        # Reset closing price and P&L if they exist
                        if "Closing_Price" in table_data[i]:
                            table_data[i]["Closing_Price"] = ""
                        if "PnL" in table_data[i]:
                            table_data[i]["PnL"] = ""
                    else:  # sell action
                        # For sell orders, record closing price and calculate P&L
                        table_data[i]["Closing_Price"] = price

                        # Calculate P&L if we have an opening price
                        if "Opening_Price" in table_data[i] and table_data[i]["Opening_Price"]:
                            opening_price = float(table_data[i]["Opening_Price"])
                            pnl = (price - opening_price) * quantity
                            table_data[i]["PnL"] = round(pnl, 2)

                            # Update Total column with total P&L
                            if "Total" not in table_data[i]:
                                table_data[i]["Total"] = round(pnl, 2)
                            else:
                                current_total = float(table_data[i]["Total"]) if table_data[i]["Total"] else 0
                                table_data[i]["Total"] = round(current_total + pnl, 2)

                        # Update quantity after selling (subtract sold shares)
                        current_quantity = int(table_data[i]["Number"]) if table_data[i]["Number"] else 0
                        table_data[i]["Number"] = max(0, current_quantity - quantity)

            # Create success message based on action
            if action == "buy":
                message = f"Order placed successfully: BUY {quantity} shares of {ticker} at ${price:.2f} (${order_amount:.2f})"
            else:
                message = f"Order placed successfully: SELL {quantity} shares of {ticker} at ${price:.2f}"
                pnl_value = 0
                for row in table_data:
                    if row["Ticker"] == ticker and "PnL" in row and row["PnL"]:
                        pnl_value = row["PnL"]
                        break

                if pnl_value != 0:
                    message += f" with P&L: ${pnl_value}"

            return dbc.Alert(
                message,
                color="success",
                dismissable=True,
            ), table_data
        else:
            return dbc.Alert(
                f"Error placing order: {result.get('message', 'Unknown error')}",
                color="danger",
                dismissable=True
            ), table_data

    # Callback to add new stock to table - work directly with the tables
    @app.callback(
        [Output("add-stock-status", "children"),
         Output("stock-table", "data", allow_duplicate=True),
         Output("order-amount-table", "data", allow_duplicate=True)],
        Input("add-stock-button", "n_clicks"),
        [State("new-ticker", "value"),
         State("stock-table", "data"),
         State("order-amount-table", "data")],
        prevent_initial_call=True
    )
    def add_stock_to_table(n_clicks, ticker, table_data, order_amount_data):
        if not n_clicks or not ticker:
            raise PreventUpdate

        # Validate ticker format
        ticker = ticker.strip().upper()
        if not ticker:
            return dbc.Alert("Please enter a valid ticker symbol", color="danger"), table_data, order_amount_data

        # Check if ticker already exists in the table
        for row in table_data:
            if row["Ticker"] == ticker:
                return dbc.Alert(f"{ticker} is already in the table", color="warning"), table_data, order_amount_data

        try:
            # Fetch stock information from the backend
            stock_info = get_stock_info(ticker)

            if not stock_info['name']:
                return dbc.Alert(f"Could not find information for {ticker}", color="danger"), table_data, order_amount_data

            # Create new row for stock table
            new_row = {
                "Name": stock_info['name'],
                "Ticker": ticker,
                "Price": "",
                "Opening_Price": "",
                "Closing_Price": "",
                "PnL": "",
                "Number": 0,
                "Original_Number": 0,
                "Total": 0,
                "Shadow_PnL": 0
            }

            # Add to stock table
            updated_table_data = table_data.copy()
            updated_table_data.append(new_row)

            # Add to order amount table
            updated_order_amount_data = order_amount_data.copy()
            updated_order_amount_data.append({
                "Ticker": ticker,
                "Amount($)": 0
            })

            # Format the data correctly for saving
            table_data_store = {}
            for row in updated_table_data:
                table_data_store[row["Name"]] = {
                    "ticker": row["Ticker"],
                    "price": str(row["Price"]) if "Price" in row and row["Price"] else "",
                    "opening_price": str(row["Opening_Price"]) if "Opening_Price" in row and row["Opening_Price"] else "",
                    "closing_price": str(row["Closing_Price"]) if "Closing_Price" in row and row["Closing_Price"] else "",
                    "pnl": str(row["PnL"]) if "PnL" in row and row["PnL"] else "",
                    "shadow_pnl": str(row["Shadow_PnL"]) if "Shadow_PnL" in row and row["Shadow_PnL"] else "",
                    "number": str(row["Number"]) if "Number" in row and row["Number"] else "0",
                    "original_number": str(row.get("Original_Number", row.get("Number", "0"))),
                    "total_pnl": str(row.get("Total", "0"))
                }

            # Save the data to disk
            save_table_data(table_data_store)

            return dbc.Alert(f"Added {ticker} to the table", color="success"), updated_table_data, updated_order_amount_data

        except Exception as e:
            return dbc.Alert(f"Error adding {ticker}: {str(e)}", color="danger"), table_data, order_amount_data

    # Callback to remove selected stocks - work directly with the tables
    @app.callback(
        [Output("selected-for-removal", "children", allow_duplicate=True),
         Output("stock-table", "data", allow_duplicate=True),
         Output("order-amount-table", "data", allow_duplicate=True)],
        Input("remove-stock-button", "n_clicks"),
        [State("stock-table", "selected_rows"),
         State("stock-table", "data"),
         State("order-amount-table", "data")],
        prevent_initial_call=True
    )
    def remove_selected_stocks(n_clicks, selected_rows, table_data, order_amount_data):
        if not n_clicks or not selected_rows:
            raise PreventUpdate

        # Get tickers to remove
        tickers_to_remove = [table_data[row]["Ticker"] for row in selected_rows]

        # Remove selected rows from stock table
        updated_table_data = [row for i, row in enumerate(table_data) if i not in selected_rows]

        # Remove corresponding rows from order amount table
        updated_order_amount_data = [row for row in order_amount_data if row["Ticker"] not in tickers_to_remove]

        # Format the data correctly for saving
        table_data_store = {}
        for row in updated_table_data:
            table_data_store[row["Name"]] = {
                "ticker": row["Ticker"],
                "price": str(row["Price"]) if "Price" in row and row["Price"] else "",
                "opening_price": str(row["Opening_Price"]) if "Opening_Price" in row and row["Opening_Price"] else "",
                "closing_price": str(row["Closing_Price"]) if "Closing_Price" in row and row["Closing_Price"] else "",
                "pnl": str(row["PnL"]) if "PnL" in row and row["PnL"] else "",
                "shadow_pnl": str(row["Shadow_PnL"]) if "Shadow_PnL" in row and row["Shadow_PnL"] else "",
                "number": str(row["Number"]) if "Number" in row and row["Number"] else "0",
                "original_number": str(row.get("Original_Number", row.get("Number", "0"))),
                "total_pnl": str(row.get("Total", "0"))
            }

        # Save the data to disk
        save_table_data(table_data_store)

        return html.P(f"Removed stocks: {', '.join(tickers_to_remove)}"), updated_table_data, updated_order_amount_data

    # Callback to update selected for removal text
    @app.callback(
        Output("selected-for-removal", "children", allow_duplicate=True),
        Input("stock-table", "selected_rows"),
        State("stock-table", "data"),
        prevent_initial_call=True
    )
    def update_selected_for_removal(selected_rows, table_data):
        if not selected_rows:
            return html.P("No stocks selected for removal")

        selected_tickers = [table_data[i]["Ticker"] for i in selected_rows]
        return html.P(f"Selected for removal: {', '.join(selected_tickers)}")

    # Callback to update the stock table with real-time prices
    @app.callback(
        Output("stock-table", "data", allow_duplicate=True),
        Input("interval-component", "n_intervals"),
        State("stock-table", "data"),
        prevent_initial_call=True
    )
    def update_stock_table_prices(n, stock_table_data):
        if not stock_table_data:
            raise PreventUpdate

        # Get all tickers from the table
        tickers = [row["Ticker"] for row in stock_table_data if "Ticker" in row]

        if not tickers:
            raise PreventUpdate

        # Fetch real-time prices from the backend
        prices = get_real_time_prices(tickers)

        # TODO: for testing: If no prices are returned, generate random prices for testing
        if prices is None or not prices or all(price is None for price in prices.values()):
            import random
            prices = {}
            for ticker in tickers:
                # Generate a random price between 10 and 1000
                prices[ticker] = round(random.uniform(10, 1000), 2)

            # Log that we're using random prices
            print("Using random prices for testing:", prices)

        if prices is None or not prices or all(price is None for price in prices.values()):
            # If we couldn't get prices, don't update
            raise PreventUpdate

        # Update prices in the stock table data
        updated = False
        for i, row in enumerate(stock_table_data):
            ticker = row.get("Ticker")
            if ticker in prices and prices[ticker] is not None:
                new_price = prices[ticker]
                current_price = row.get("Price", "")

                # Convert current_price to float for comparison if it's not empty
                if current_price and isinstance(current_price, str):
                    try:
                        current_price = float(current_price)
                    except ValueError:
                        current_price = 0

                # Compare and update if different
                if new_price != current_price:
                    stock_table_data[i]["Price"] = new_price
                    updated = True

                    # Calculate P&L if we have opening price and shares
                    if "Opening_Price" in row and row["Opening_Price"] and "Number" in row and row["Number"]:
                        try:
                            opening_price = float(row["Opening_Price"])
                            shares = int(row["Number"])
                            if shares > 0:
                                # Calculate unrealized P&L
                                pnl = (new_price - opening_price) * shares
                                stock_table_data[i]["PnL"] = round(pnl, 2)
                        except (ValueError, TypeError):
                            pass
                
                # Calculate Shadow P&L based on opening price and current price
                # This will show potential P&L even if position is closed
                if "Opening_Price" in row and row["Opening_Price"]:
                    try:
                        opening_price = float(row["Opening_Price"])
                        # Use original position size if available, otherwise use current number
                        original_shares = int(row.get("Original_Number", row.get("Number", 0)))
                        if original_shares > 0:
                            shadow_pnl = (new_price - opening_price) * original_shares
                            stock_table_data[i]["Shadow_PnL"] = round(shadow_pnl, 2)
                    except (ValueError, TypeError):
                        pass

        if not updated:
            # If no prices were updated, don't update the table
            raise PreventUpdate

        # Save the updated table data to disk
        table_data_store = {}
        for row in stock_table_data:
            table_data_store[row["Name"]] = {
                "ticker": row["Ticker"],
                "price": str(row["Price"]) if "Price" in row and row["Price"] else "",
                "opening_price": str(row["Opening_Price"]) if "Opening_Price" in row and row["Opening_Price"] else "",
                "closing_price": str(row["Closing_Price"]) if "Closing_Price" in row and row["Closing_Price"] else "",
                "pnl": str(row["PnL"]) if "PnL" in row and row["PnL"] else "",
                "shadow_pnl": str(row["Shadow_PnL"]) if "Shadow_PnL" in row and row["Shadow_PnL"] else "",
                "number": str(row["Number"]) if "Number" in row and row["Number"] else "0",
                "original_number": str(row.get("Original_Number", row.get("Number", "0"))),
                "total_pnl": str(row.get("Total", "0"))
            }

        # Save the data to disk
        save_table_data(table_data_store)

        # Return the updated table data
        return stock_table_data

    # Add this callback to ensure order amount table stays in sync with stock table
    @app.callback(
        Output("order-amount-table", "data"),
        Input("stock-table", "data"),
        State("order-amount-table", "data"),
        prevent_initial_call=True
    )
    def sync_order_amount_table(stock_table_data, order_amount_data):
        """Ensure order amount table has exactly one row for each stock in the main table"""
        if not stock_table_data:
            return []

        # Create a dictionary of existing order amounts by ticker
        existing_amounts = {}
        for row in order_amount_data:
            if "Ticker" in row and "Amount($)" in row:
                existing_amounts[row["Ticker"]] = row["Amount($)"]

        # Create new order amount data with one row per stock
        new_order_amount_data = []
        for stock_row in stock_table_data:
            ticker = stock_row.get("Ticker")
            if ticker:
                # Use existing amount if available, otherwise default to 0
                amount = existing_amounts.get(ticker, 0)
                new_order_amount_data.append({
                    "Ticker": ticker,
                    "Amount($)": amount
                })

        return new_order_amount_data