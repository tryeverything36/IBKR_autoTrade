import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash_app.utils.data import create_dataframe

def create_layout(initial_data=None):
    """Create the main layout of the application optimized for mobile"""
    # Use empty dict if no initial data is provided
    if initial_data is None:
        initial_data = {}
    
    # Create initial table data
    initial_table_data = create_dataframe(initial_data).to_dict('records') if initial_data else []
    
    # Create initial order amount data matching the structure of the stock table
    initial_order_data = []
    for row in initial_table_data:
        initial_order_data.append({
            "Ticker": row["Ticker"],
            "Amount($)": 0
        })
    
    layout = html.Div([
        # Header with logo and title - simplified for mobile
        dbc.Navbar(
            dbc.Container([
                html.Div([
                    html.I(className="fas fa-chart-line me-2", style={"font-size": "20px"}),
                    html.H3("AutoTrader", className="mb-0 ms-2")
                ], style={"display": "flex", "align-items": "center"}),
                # Connection status in the navbar
                html.Div(id="connection-status", className="ms-auto")
            ]),
            color="dark",
            dark=True,
            className="mb-2"
        ),

        dbc.Container([
            # Tabs for different pages with improved styling for mobile
            dbc.Tabs([
                # Trading Tab
                dbc.Tab(label="Trading", children=[
                    # Main content area - tables side by side
                    dbc.Row([
                        # Combined card for stock and order amount tables
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5("Stock Portfolio", className="mb-0"),
                                ]),
                                dbc.CardBody([
                                    # Stock tables side by side in the same card
                                    dbc.Row([
                                        # Stock table column
                                        dbc.Col([
                                            # Stock table with mobile-friendly styling
                                            dash_table.DataTable(
                                                id='stock-table',
                                                columns=[
                                                    {"name": "Name", "id": "Name"},
                                                    {"name": "Price", "id": "Price", "type": "numeric", "format": {"specifier": "$.2f"}},
                                                    {"name": "Open", "id": "Opening_Price", "type": "numeric", "format": {"specifier": "$.2f"}},
                                                    {"name": "Close", "id": "Closing_Price", "type": "numeric", "format": {"specifier": "$.2f"}},
                                                    {"name": "P&L", "id": "PnL", "type": "numeric", "format": {"specifier": "$.2f"}},
                                                    {"name": "Shadow", "id": "Shadow_PnL", "type": "numeric", "format": {"specifier": "$.2f"}},
                                                    {"name": "Qty", "id": "Number", "editable": True},
                                                ],
                                                data=initial_table_data,
                                                row_selectable="multi",
                                                editable=True,
                                                style_table={'overflowX': 'hidden', 'overflowY': 'auto', 'maxHeight': '600px'},
                                                style_cell={
                                                    'textAlign': 'center',
                                                    'padding': '1px',
                                                    'fontFamily': 'Arial, sans-serif',
                                                    'fontSize': '10px',
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis',
                                                    'maxWidth': '0',  # Force equal column width
                                                },
                                                style_cell_conditional=[
                                                    {'if': {'column_id': 'Name'}, 'width': '20%', 'minWidth': '45px'},
                                                    {'if': {'column_id': 'Price'}, 'width': '14%', 'minWidth': '35px'},
                                                    {'if': {'column_id': 'Opening_Price'}, 'width': '14%', 'minWidth': '35px'},
                                                    {'if': {'column_id': 'Closing_Price'}, 'width': '14%', 'minWidth': '35px'},
                                                    {'if': {'column_id': 'PnL'}, 'width': '14%', 'minWidth': '35px'},
                                                    {'if': {'column_id': 'Shadow_PnL'}, 'width': '14%', 'minWidth': '35px'},
                                                    {'if': {'column_id': 'Number'}, 'width': '10%', 'minWidth': '30px'},
                                                ],
                                                css=[
                                                    {
                                                        'selector': '.dash-cell div.dash-cell-value',
                                                        'rule': 'display: inline; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'
                                                    },
                                                    {
                                                        'selector': '.dash-spreadsheet-container .dash-spreadsheet-inner table',
                                                        'rule': 'width: 100% !important; table-layout: fixed !important;'
                                                    }
                                                ],
                                                style_header={
                                                    'backgroundColor': '#f0f2f6',
                                                    'fontWeight': 'bold',
                                                    'border': '1px solid #ddd',
                                                    'textAlign': 'center',
                                                    'fontSize': '10px',
                                                    'padding': '1px',
                                                    'height': '20px',
                                                    'whiteSpace': 'nowrap',
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis',
                                                },
                                                style_data={
                                                    'whiteSpace': 'nowrap',
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis',
                                                    'height': '20px',
                                                    'minHeight': '20px',
                                                },
                                                page_action='none',  # Disable pagination
                                            ),
                                        ], width=10),
                                        
                                        # Order amount table column - in the same card
                                        dbc.Col([
                                            # Order amount table
                                            dash_table.DataTable(
                                                id='order-amount-table',
                                                columns=[
                                                    {"name": "Amt($)", "id": "Amount($)", "type": "numeric",
                                                     "editable": True},
                                                ],
                                                data=initial_order_data,
                                                style_table={'overflowX': 'hidden', 'overflowY': 'auto', 'maxHeight': '600px'},  # Match main table height
                                                style_cell={
                                                    'textAlign': 'center',
                                                    'padding': '1px',  # Match main table padding
                                                    'fontFamily': 'Arial, sans-serif',
                                                    'fontSize': '10px',  # Match main table font size
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis',
                                                    'minWidth': '100%',
                                                    'width': '100%',
                                                    'maxWidth': '100%',
                                                    'height': '20px',  # Match main table row height
                                                    'minHeight': '20px',  # Match main table row height
                                                },
                                                style_header={
                                                    'backgroundColor': '#f0f2f6',
                                                    'fontWeight': 'bold',
                                                    'border': '1px solid #ddd',
                                                    'textAlign': 'center',
                                                    'fontSize': '10px',  # Match main table header font size
                                                    'padding': '1px',  # Match main table header padding
                                                    'height': '20px',  # Match main table header height
                                                    'whiteSpace': 'nowrap',
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis',
                                                },
                                                style_data={
                                                    'whiteSpace': 'nowrap',
                                                    'overflow': 'hidden',
                                                    'textOverflow': 'ellipsis',
                                                    'height': '20px',
                                                    'minHeight': '20px',
                                                },
                                                page_action='none',  # Disable pagination to match main table
                                            ),
                                        ], width=2),
                                    ]),
                                ])
                            ], className="mb-3 shadow-sm"),
                        ], width=12),  # Full width for the combined card
                        
                        # Buy/Sell buttons - full width for mobile
                        dbc.Col([
                            dbc.Row([
                                dbc.Col(
                                    dbc.Button(
                                        [html.I(className="fas fa-shopping-cart me-2"), "Buy"], 
                                        id="buy-button", 
                                        color="success", 
                                        className="w-100 mb-2"
                                    ),
                                    width=6
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        [html.I(className="fas fa-cash-register me-2"), "Sell"], 
                                        id="sell-button", 
                                        color="danger", 
                                        className="w-100 mb-2"
                                    ),
                                    width=6
                                )
                            ]),
                        ], width=12),
                        
                        # Order controls - simplified for mobile
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5("Order Controls", className="mb-0"),
                                ]),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label("Trailing Stop %", className="fw-bold"),
                                            dbc.InputGroup([
                                                dbc.InputGroupText(html.I(className="fas fa-percentage")),
                                                dbc.Input(id="trailing-stop", type="number", value=2.0, min=0.1, step=0.1)
                                            ])
                                        ], width=12),
                                    ]),
                                    # Notification area
                                    html.Div(id="notification-area", className="mt-3")
                                ])
                            ], className="mb-3 shadow-sm")
                        ], width=12),
                        
                        # Table management - simplified for mobile
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5("Manage Portfolio", className="mb-0"),
                                ]),
                                dbc.CardBody([
                                    # Add stock section
                                    html.H6("Add Stock", className="mb-2"),
                                    dbc.InputGroup([
                                        dbc.Input(id="new-ticker", placeholder="Ticker Symbol"),
                                        dbc.Button(
                                            [html.I(className="fas fa-plus")], 
                                            id="add-stock-button", 
                                            color="primary"
                                        )
                                    ], className="mb-3"),
                                    html.Div(id="add-stock-status", className="mb-3"),
                                    
                                    # Remove stock section
                                    html.H6("Remove Selected", className="mb-2"),
                                    html.Div(id="selected-for-removal", className="mb-2 text-info"),
                                    dbc.Button(
                                        [html.I(className="fas fa-trash-alt me-2"), "Remove"], 
                                        id="remove-stock-button", 
                                        color="danger", 
                                        className="w-100"
                                    )
                                ])
                            ], className="mb-3 shadow-sm"),
                        ], width=12),
                    ], className="g-2"),  # Reduce gutter spacing for mobile
                ], className="p-1"),  # Reduce padding for mobile
            ], className="mb-2"),
        ], fluid=True, className="px-1 py-1"),  # Reduce padding for mobile

        # Store components for maintaining state
        dcc.Store(id='table-data-store', data=initial_data),
        dcc.Store(id='order-amount-store', data={}),
        dcc.Store(id='selected-ticker-store', data=None),
        dcc.Store(id='price-history-store', data={}),
        dcc.Store(id='settings-store', data={}),
        dcc.Store(id='active-timeframe', data="1D"),
        
        # Interval component for updates
        dcc.Interval(
            id='interval-component',
            interval=20 * 1000,
            n_intervals=0
        ),
        
        # Footer - simplified for mobile
        html.Footer(
            dbc.Container([
                html.Hr(),
                html.P("© 2025 AutoTrader - Interactive Brokers Trading Dashboard", className="text-center text-muted")
            ]),
            className="mt-3"
        ),
        
        # Hidden divs for data management
        dcc.Store(id="data-change-timestamp"),
        dcc.Store(id="save-status"),
    ])
    
    return layout