import yaml
import os
from typing import List

class MonitorConfig:
    def __init__(self, config_path='.monitor_config.yaml'):
        self.ignore_patterns: List[str] = []
        self.file_extensions: List[str] = ['.py']

        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.ignore_patterns = config.get('ignore_patterns', [])
                self.file_extensions = config.get('file_extensions_to_check', ['.py'])

CONFIG = MonitorConfig()