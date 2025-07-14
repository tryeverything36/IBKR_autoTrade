import yaml
import os
from pathlib import Path

def load_config(config_path=None):
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    else:
        # Default configuration
        return {
            "ibkr": {
                "host": "127.0.0.1",
                "port": 7497,  # 7497 for TWS paper trading, 7496 for TWS live, 4002 for Gateway
                "client_id": 1
            },
            "trading": {
                "default_trailing_stop_percentage": 2.0,
                "check_interval_seconds": 5
            }
        }
