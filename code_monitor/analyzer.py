import git
import os
from itertools import chain
import fnmatch
from typing import Dict, List, Any
from .config import CONFIG
from .utils import get_functions_and_classes

class RepoAnalyzer:
    """Analyzes a Git repository for code changes at the object level."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            print(f"Error: '{repo_path}' is not a valid Git repository.")
            raise

    def _is_ignored(self, file_path: str) -> bool:
        """Checks if a file path matches any of the ignore patterns."""
        for pattern in CONFIG.ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

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
        
    def _get_file_content(self, commit_hash: str, file_path: str) -> str:
        """Retrieves the content of a file from a specific commit."""
        try:
            commit = self.repo.commit(commit_hash)
            blob = commit.tree / file_path
            return blob.data_stream.read().decode('utf-8', 'ignore')
        except (KeyError, git.exc.GitCommandError):
            return ""  # File did not exist in this commit

    def analyze_changes(self, staged_only: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes file changes to identify added, removed, and modified objects.
        
        Args:
            staged_only (bool): If True, analyzes only staged changes. 
                                Otherwise, analyzes all uncommitted changes.
        """
        head_commit = self.repo.head.commit

        if staged_only:
            # Compare HEAD vs index (staged changes)
            diffs = self.repo.index.diff("HEAD", R=True)
            untracked_files = []
        else:
            # Combine staged (HEAD vs index) and unstaged (index vs working tree)
            staged_diffs = self.repo.index.diff("HEAD", R=True)
            unstaged_diffs = self.repo.index.diff(None)
            diffs = list(chain(staged_diffs, unstaged_diffs))
            # Include untracked files as added
            untracked_files = list(self.repo.untracked_files)
        
        analysis_results = {}

        for diff in diffs:
            file_path = diff.a_path or diff.b_path
            
            # Skip ignored files and non-specified extensions
            if self._is_ignored(file_path) or not any(file_path.endswith(ext) for ext in CONFIG.file_extensions):
                continue
            
            old_content = self._get_file_content("HEAD", file_path) if diff.change_type != 'A' else ""

            # Determine working tree path for the new content (if it exists)
            new_path = diff.b_path or diff.a_path
            new_content = ""
            if diff.change_type != 'D' and new_path:
                working_tree_path = os.path.join(self.repo.working_dir, new_path)
                if os.path.exists(working_tree_path):
                    with open(working_tree_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()

            old_objects = get_functions_and_classes(old_content)
            new_objects = get_functions_and_classes(new_content)

            added = {k: v for k, v in new_objects.items() if k not in old_objects}
            removed = {k: v for k, v in old_objects.items() if k not in new_objects}
            
            # Rudimentary check for modification (object exists in both but content differs)
            # A more advanced check would compare function bodies line by line.
            modified = {
                k: v for k, v in new_objects.items()
                if k in old_objects and new_objects[k] != old_objects[k]
            }

            # Always record the file-level change, even if no object-level changes
            analysis_results[file_path] = {
                "status": diff.change_type,
                "added": list(added.values()),
                "removed": list(removed.values()),
                "modified": list(modified.values()),
            }

        # Handle untracked files (only when not staged_only)
        for file_path in untracked_files:
            if self._is_ignored(file_path) or not any(file_path.endswith(ext) for ext in CONFIG.file_extensions):
                continue
            working_tree_path = os.path.join(self.repo.working_dir, file_path)
            if not os.path.exists(working_tree_path):
                continue
            with open(working_tree_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            new_objects = get_functions_and_classes(new_content)
            analysis_results[file_path] = {
                "status": 'A',
                "added": list(new_objects.values()),
                "removed": [],
                "modified": [],
            }

        return analysis_results
