"""
Unit tests for repository exploration tools.
"""

import tempfile
from pathlib import Path
import pytest
from agent.tools.repository_tools import (
    list_files, read_file_snippet, search_symbol, find_test_files, create_unified_diff
)

def test_list_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "module_a.py").write_text("x = 1\n", encoding="utf-8")
        (tmp / "subdir").mkdir()
        (tmp / "subdir" / "module_b.py").write_text("y = 2\n", encoding="utf-8")
        (tmp / ".git").mkdir()
        (tmp / ".git" / "ignored.py").write_text("z = 3\n", encoding="utf-8")

        files = list_files(str(tmp))
        assert "module_a.py" in files
        assert "subdir/module_b.py" in files
        assert not any(".git" in f for f in files)

def test_read_file_snippet():
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".py", encoding="utf-8") as f:
        f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")
        temp_name = f.name

    try:
        snippet = read_file_snippet(temp_name, start_line=2, end_line=4)
        assert snippet["start_line"] == 2
        assert snippet["end_line"] == 4
        assert snippet["total_lines"] == 5
        assert "line 2\nline 3\nline 4\n" == snippet["content"]
        assert "2 | line 2" in snippet["formatted_content"]
    finally:
        Path(temp_name).unlink(missing_ok=True)

def test_search_symbol():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "calc.py").write_text("def calculate_sum(a, b):\n    return a + b\n", encoding="utf-8")
        matches = search_symbol(str(tmp), "calculate_sum")
        assert len(matches) == 1
        assert matches[0]["file"] == "calc.py"
        assert matches[0]["line_number"] == 1

def test_create_unified_diff():
    orig = "def foo():\n    return 1\n"
    mod = "def foo():\n    return 2\n"
    diff = create_unified_diff(orig, mod, "test.py")
    assert "--- a/test.py" in diff
    assert "+++ b/test.py" in diff
    assert "-    return 1" in diff
    assert "+    return 2" in diff
