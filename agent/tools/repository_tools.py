"""
Repository Tools for CodeGuardian Agent.
Provides file discovery, symbol search, code extraction, and diff utilities.
"""

import os
import re
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_EXCLUDES = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".idea", ".vscode", "dist", "build", "egg-info"
}

def list_files(
    repo_path: str,
    file_extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    max_depth: int = 5
) -> List[str]:
    """Lists source code files in a repository recursively within a given depth."""
    excludes = DEFAULT_EXCLUDES.union(set(exclude_dirs or []))
    repo = Path(repo_path).resolve()
    valid_files: List[str] = []

    if not repo.exists():
        return valid_files

    extensions = tuple(file_extensions) if file_extensions else (".py", ".json", ".yaml", ".yml", ".toml", ".md")

    for root, dirs, files in os.walk(repo):
        rel_root = Path(root).relative_to(repo)
        if len(rel_root.parts) > max_depth:
            continue
        dirs[:] = [d for d in dirs if d not in excludes and not d.startswith(".")]

        for file in files:
            if file.endswith(extensions):
                rel_path = str(rel_root / file).replace("\\", "/")
                if rel_path.startswith("./"):
                    rel_path = rel_path[2:]
                valid_files.append(rel_path)

    return sorted(valid_files)

def read_file_snippet(file_path: str, start_line: int = 1, end_line: Optional[int] = None) -> Dict[str, Any]:
    """Reads a range of lines from a file with 1-based indexing and returns lines with line numbers."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    start_idx = max(1, start_line)
    end_idx = min(total_lines, end_line) if end_line is not None else total_lines

    selected = all_lines[start_idx - 1:end_idx]
    formatted = [f"{start_idx + i:4d} | {line}" for i, line in enumerate(selected)]

    return {
        "file_path": str(path).replace("\\", "/"),
        "start_line": start_idx,
        "end_line": end_idx,
        "total_lines": total_lines,
        "content": "".join(selected),
        "formatted_content": "".join(formatted)
    }

def search_symbol(repo_path: str, symbol_name: str, regex: bool = False) -> List[Dict[str, Any]]:
    """Searches for a symbol (function, class, or variable) across all python files."""
    repo = Path(repo_path).resolve()
    py_files = list_files(str(repo), file_extensions=[".py"])
    matches = []

    pattern = symbol_name if regex else re.escape(symbol_name)
    compiled = re.compile(rf"\b{pattern}\b")

    for rel_path in py_files:
        full_path = repo / rel_path
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                for idx, line in enumerate(f, start=1):
                    if compiled.search(line):
                        matches.append({
                            "file": rel_path,
                            "line_number": idx,
                            "line_text": line.strip()
                        })
        except Exception:
            continue

    return matches

def find_test_files(repo_path: str, target_module: Optional[str] = None) -> List[str]:
    """Locates test files relevant to the target module or repository."""
    py_files = list_files(repo_path, file_extensions=[".py"])
    test_files = [
        f for f in py_files
        if f.startswith("tests/") or f.startswith("test/") or "/test_" in f or f.endswith("_test.py") or f.startswith("test_")
    ]

    if not target_module:
        return test_files

    # Prioritize tests matching target module name
    base_name = Path(target_module).stem
    prioritized = [f for f in test_files if base_name in f]
    remaining = [f for f in test_files if f not in prioritized]
    return prioritized + remaining

def create_unified_diff(original_text: str, modified_text: str, file_path: str) -> str:
    """Generates a standard unified git diff format between original and modified text."""
    clean_path = file_path.replace("\\", "/")
    orig_lines = original_text.splitlines(keepends=True)
    mod_lines = modified_text.splitlines(keepends=True)

    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{clean_path}",
        tofile=f"b/{clean_path}",
        lineterm="\n"
    )
    return "".join(diff)
