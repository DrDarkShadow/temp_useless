import ast
from typing import List, Tuple, Dict, Any

def get_functions_and_classes(code_content: str) -> Dict[str, Dict[str, Any]]:
    """
    Parses Python code content to extract information about functions and classes.
    """
    try:
        tree = ast.parse(code_content)
    except SyntaxError:
        # If file has syntax errors, return empty so it doesn't break analysis
        return {}
    objects = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            obj_type = "Class" if isinstance(node, ast.ClassDef) else "Function"
            objects[node.name] = {
                "type": obj_type,
                "name": node.name,
                "start_line": node.lineno,
                "end_line": node.end_lineno
            }
    return objects