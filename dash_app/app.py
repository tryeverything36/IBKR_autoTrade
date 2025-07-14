import dash
import dash_bootstrap_components as dbc
from dash_app.utils.data import load_table_data
from dash_app.components.layout import create_layout
from dash_app.components.callbacks import register_callbacks

def create_app():
    """Create and configure the Dash application"""
    # Initialize the Dash app with Bootstrap styling and Font Awesome
    app = dash.Dash(
        __name__, 
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
        ],
        meta_tags=[
            # This meta tag ensures proper scaling on mobile devices
            {"name": "viewport", "content": "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"}
        ]
    )

    # Set the browser tab title
    app.title = "AutoTrader"
    
    # Load saved data
    initial_data = load_table_data()
    
    # Set the app layout with initial data
    app.layout = create_layout(initial_data)
    
    # Register callbacks
    register_callbacks(app)
    
    return app

# Create the app
app = create_app()

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8501, host='0.0.0.0')