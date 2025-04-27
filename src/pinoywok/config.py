# config.py
from dotenv import load_dotenv
from pathlib import Path
import yaml
from pinoywok.args import args
import json
class Config:
    _instance = None
    _config = None

    def load_config(self,file_path):
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        self._config = config
        return config
    
    def get_config(self,key):
    
        """Get a config value using a dot-separated key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Config key '{key}' not found")
        return value
    
    def get(self,key):
    
        """Get a config value using a dot-separated key"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Config key '{key}' not found")
        return value
    
    
    def __new__(self):
        if self._instance is None:
            self._instance = super(Config, self).__new__(self)
            self._instance = Config()
            #self._instance.load_config(file)
        return self._instance

    def to_str(self):
        return yaml.dump(self._config, default_flow_style=False)
    
    def to_json(self):
        return json.dumps(self._config, indent=4)
    
config = Config()
