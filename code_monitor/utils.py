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

def hello(name):
    print(name)


def calculate_fibonacci(n):
    """
    Calculates the n-th Fibonacci number using an iterative approach.

    This function is designed to be a clear example of a new, distinct piece of logic
    added to test the documentation agent's ability to intelligently place
    new documentation snippets.

    Args:
        n (int): The position in the Fibonacci sequence.

    Returns:
        int: The n-th Fibonacci number.
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
