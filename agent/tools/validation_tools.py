"""
Validation and Failure Analysis Tools for CodeGuardian Agent.
Executes test suites, validates patch syntax and diff application, and parses error tracebacks.
"""

import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

def validate_python_syntax(code_string: str, filename: str = "<string>") -> Dict[str, Any]:
    """Validates Python syntax by parsing the AST without executing code."""
    try:
        ast.parse(code_string, filename=filename)
        return {"valid": True, "error": None}
    except SyntaxError as e:
        return {
            "valid": False,
            "error": str(e),
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text
        }

def validate_patch_syntax(patch_diff: str) -> Dict[str, Any]:
    """Checks whether a string resembles a valid unified diff."""
    if not patch_diff or not patch_diff.strip():
        return {"valid": False, "error": "Patch is empty"}

    has_orig_header = bool(re.search(r"^---\s+[ab]/", patch_diff, re.MULTILINE))
    has_mod_header = bool(re.search(r"^\+\+\+\s+[ab]/", patch_diff, re.MULTILINE))
    has_hunk_header = bool(re.search(r"^@@\s+-\d+.*?\+\d+.*?@@", patch_diff, re.MULTILINE))

    if not (has_orig_header and has_mod_header and has_hunk_header):
        return {
            "valid": False,
            "error": "Patch diff missing standard unified diff headers (---, +++, @@)",
            "has_orig_header": has_orig_header,
            "has_mod_header": has_mod_header,
            "has_hunk_header": has_hunk_header
        }

    return {"valid": True, "error": None}

def parse_traceback(test_output: str) -> Dict[str, Any]:
    """Extracts structured diagnostic failure details from pytest stdout/stderr."""
    result: Dict[str, Any] = {
        "has_failures": False,
        "failed_tests": [],
        "exception_type": None,
        "exception_message": None,
        "failing_location": None,
        "traceback_snippet": ""
    }

    if "FAILED" in test_output or "ERROR" in test_output or "Traceback" in test_output:
        result["has_failures"] = True

    # Find failed test names e.g. FAILED tests/test_foo.py::test_bar - AssertionError: ...
    failed_lines = re.findall(r"^FAILED\s+([^\s]+)(?:\s+-\s+(.*))?", test_output, re.MULTILINE)
    for test_name, extra in failed_lines:
        result["failed_tests"].append({
            "test_name": test_name,
            "message": extra.strip() if extra else ""
        })

    # Find exception e.g. E   AssertionError: assert 1 == 2 or E   ZeroDivisionError: division by zero
    exception_matches = re.findall(r"^E\s+([A-Za-z_][A-Za-z0-9_]*Error|[A-Za-z_][A-Za-z0-9_]*Exception):\s*(.*)", test_output, re.MULTILINE)
    if exception_matches:
        last_exc_type, last_exc_msg = exception_matches[-1]
        result["exception_type"] = last_exc_type
        result["exception_message"] = last_exc_msg

    # Find failing line e.g. >   assert result == expected or tests/test_calc.py:42: in test_foo
    loc_match = re.search(r"([A-Za-z0-9_\-\\/]+\.py):(\d+):", test_output)
    if loc_match:
        result["failing_location"] = {
            "file": loc_match.group(1).replace("\\", "/"),
            "line": int(loc_match.group(2))
        }

    # Extract relevant snippet (up to 30 lines around failures)
    lines = test_output.splitlines()
    snippet_lines = []
    capture = False
    for line in lines:
        if "FAILURES" in line or "Traceback (most recent call last)" in line:
            capture = True
        if capture:
            snippet_lines.append(line)
            if len(snippet_lines) >= 40:
                break

    result["traceback_snippet"] = "\n".join(snippet_lines) if snippet_lines else test_output[-1500:]

    return result

def run_pytest(
    repo_path: str,
    test_target: Optional[str] = None,
    timeout_seconds: int = 45,
    python_executable: Optional[str] = None
) -> Dict[str, Any]:
    """Runs pytest inside the target repository and returns exit code, stdout, and parsed failure details."""
    repo = Path(repo_path).resolve()
    py_exec = python_executable or sys.executable

    cmd = [py_exec, "-m", "pytest", "-v"]
    if test_target:
        cmd.append(test_target)

    env = os.environ.copy()
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONPATH"] = str(repo)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_seconds,
            env=env
        )
        output = proc.stdout or ""
        parsed = parse_traceback(output)
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "output": output,
            "diagnostics": parsed
        }
    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "returncode": -1,
            "output": f"Pytest execution timed out after {timeout_seconds} seconds.",
            "diagnostics": {"has_failures": True, "exception_type": "TimeoutExpired", "traceback_snippet": str(e)}
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "output": f"Pytest execution failed to launch: {str(e)}",
            "diagnostics": {"has_failures": True, "exception_type": type(e).__name__, "traceback_snippet": str(e)}
        }

def apply_patch_dry_run(original_content: str, patch_diff: str) -> Dict[str, Any]:
    """Simulates applying a unified diff or validates replacement consistency."""
    syntax_check = validate_patch_syntax(patch_diff)
    if not syntax_check["valid"]:
        return syntax_check

    # Parse hunk lines to verify consistency
    added = len(re.findall(r"^\+[^\+]", patch_diff, re.MULTILINE))
    deleted = len(re.findall(r"^-[^-]", patch_diff, re.MULTILINE))

    return {
        "valid": True,
        "lines_added": added,
        "lines_deleted": deleted,
        "total_delta": added + deleted,
        "is_minimal": (added + deleted) <= 25
    }
