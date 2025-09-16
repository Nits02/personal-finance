import yaml
import os

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.yaml')

_config = None

def get_config():
    global _config
    if _config is None:
        with open(_CONFIG_PATH, 'r') as f:
            _config = yaml.safe_load(f)
    return _config
