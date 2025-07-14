from dash_app.app import create_app

# Create and run the app
if __name__ == '__main__':
    app = create_app()
    app.run_server(debug=True, port=8501, host='0.0.0.0')