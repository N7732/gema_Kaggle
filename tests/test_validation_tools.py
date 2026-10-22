"""
Unit tests for validation and failure diagnostics tools.
"""

from agent.tools.validation_tools import (
    validate_python_syntax, validate_patch_syntax, parse_traceback, apply_patch_dry_run
)

def test_validate_python_syntax():
    valid_res = validate_python_syntax("x = 10\ndef foo(): pass\n")
    assert valid_res["valid"] is True

    invalid_res = validate_python_syntax("def foo( missing_paren:\n    pass")
    assert invalid_res["valid"] is False
    assert "error" in invalid_res

def test_validate_patch_syntax():
    good_diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,3 +1,3 @@\n"
        "-old\n"
        "+new\n"
    )
    assert validate_patch_syntax(good_diff)["valid"] is True

    bad_diff = "Just some text without diff headers"
    assert validate_patch_syntax(bad_diff)["valid"] is False

def test_parse_traceback():
    sample_pytest_out = """
=================================== FAILURES ===================================
______________________________ test_divide_zero _______________________________

    def test_divide_zero():
>       assert safe_divide(10, 0) == 0.0
E       ZeroDivisionError: division by zero

calculator/test_divider.py:12: ZeroDivisionError
=========================== short test summary info ============================
FAILED calculator/test_divider.py::test_divide_zero - ZeroDivisionError: division by zero
1 failed, 2 passed in 0.05s
"""
    parsed = parse_traceback(sample_pytest_out)
    assert parsed["has_failures"] is True
    assert parsed["exception_type"] == "ZeroDivisionError"
    assert len(parsed["failed_tests"]) == 1
    assert parsed["failed_tests"][0]["test_name"] == "calculator/test_divider.py::test_divide_zero"

def test_apply_patch_dry_run():
    diff = (
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,2 +1,3 @@\n"
        "-orig\n"
        "+new1\n"
        "+new2\n"
    )
    res = apply_patch_dry_run("orig", diff)
    assert res["valid"] is True
    assert res["lines_added"] == 2
    assert res["lines_deleted"] == 1
    assert res["total_delta"] == 3
    assert res["is_minimal"] is True
