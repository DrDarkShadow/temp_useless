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


def sub_num(a: int, b: int) -> int:
    """
    Subtracts the second integer from the first.

    Parameters:
        a (int): The number from which `b` will be subtracted.
        b (int): The number to subtract from `a`.

    Returns:
        int: The result of subtracting b from a.

    Example:
        >>> sub_num(10, 3)
        7
    """
    return a - b


CONFIG = MonitorConfig()
