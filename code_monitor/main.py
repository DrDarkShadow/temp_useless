import click
from colorama import Fore, Style, init
try:
    # When executed as module: python -m code_monitor.main
    from .analyzer import RepoAnalyzer
except ImportError:
    # When executed directly: python code_monitor/main.py
    from analyzer import RepoAnalyzer

init(autoreset=True)

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


def add_numbers(a: int, b: int) -> int:
    """
    Adds two integers and returns the result.

    Parameters:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The sum of a and b.

    Example:
        >>> add_numbers(3, 5)
        8
    """
    return a + b


def sub_numbers(a: int, b: int) -> int:
    """
    Substract two integers and returns the result.

    Parameters:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The diff of a and b.

    Example:
        >>> sub_numbers(5, 3)
        2
    """
    return a - b

def print_analysis(results: dict):
    """Prints the analysis results in a readable format."""
    if not results:
        click.echo(Fore.GREEN + "No relevant code changes detected.")
        return

    for file_path, data in results.items():
        status_color = {
            'A': Fore.GREEN, 'M': Fore.YELLOW, 'D': Fore.RED,
        }.get(data['status'], Fore.WHITE)
        click.echo(status_color + f"\n--- Changes in {file_path} [{data['status']}] ---")

        if data['added']:
            click.echo(Fore.GREEN + "  [+] Added:")
            for item in data['added']:
                click.echo(f"      - {item['type']}: {item['name']} (lines {item['start_line']}-{item['end_line']})")
        
        if data['removed']:
            click.echo(Fore.RED + "  [-] Removed:")
            for item in data['removed']:
                click.echo(f"      - {item['type']}: {item['name']}")

        if data['modified']:
            click.echo(Fore.YELLOW + "  [*] Modified:")
            for item in data['modified']:
                click.echo(f"      - {item['type']}: {item['name']} (lines {item['start_line']}-{item['end_line']})")

    summary_msg = f"\nSummary: Analyzed {len(results)} files."
    click.echo(Style.BRIGHT + summary_msg)


@click.command()
@click.option('--path', default='.', help='Path to the Git repository.')
@click.option('--staged-only', is_flag=True, default=False, help='Only analyze staged files (for pre-commit hooks).')
def analyze(path, staged_only):
    """
    Analyzes a Git repository for function and class level changes.
    By default, it shows all uncommitted changes.
    Use --staged-only for pre-commit hooks.
    """
    try:
        analyzer = RepoAnalyzer(repo_path=path)
        results = analyzer.analyze_changes(staged_only=staged_only)
        print_analysis(results)
    except Exception as e:
        click.echo(Fore.RED + f"An error occurred: {e}", err=True)

if __name__ == "__main__":
    analyze()
