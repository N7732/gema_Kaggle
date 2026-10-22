"""
Benchmark test cases representing common SWE-bench style defects.
Each case contains a buggy codebase template, a bug report, and ground truth tests.
"""

BENCHMARK_TASKS = [
    {
        "id": "task_01_zerodiv",
        "name": "ZeroDivision in Safe Divider Utility",
        "description": "SafeDivider.divide crashes with ZeroDivisionError when denominator is zero instead of returning fallback default_val.",
        "files": {
            "calculator/divider.py": '''"""Divider module."""

def safe_divide(numerator: float, denominator: float, default_val: float = 0.0) -> float:
    """Safely divide two numbers, returning default_val if denominator is 0."""
    return numerator / denominator
''',
            "tests/test_divider.py": '''import pytest
from calculator.divider import safe_divide

def test_divide_normal():
    assert safe_divide(10, 2) == 5.0

def test_divide_zero_fallback():
    assert safe_divide(10, 0, default_val=-1.0) == -1.0

def test_divide_zero_default():
    assert safe_divide(5, 0) == 0.0
'''
        },
        "target_symbol": "safe_divide",
        "target_file": "calculator/divider.py"
    },
    {
        "id": "task_02_pagination_off_by_one",
        "name": "Off-by-One in Pagination Slicing",
        "description": "paginate_items fails to include the final item on the boundary due to incorrect index offset calculation.",
        "files": {
            "utils/pagination.py": '''"""Pagination utilities."""
from typing import List, Any

def paginate_items(items: List[Any], page: int, page_size: int) -> List[Any]:
    """Returns items for a 1-indexed page number."""
    if page < 1:
        page = 1
    start_idx = (page - 1) * page_size
    # Bug: end_idx stops one item short
    end_idx = start_idx + page_size - 1
    return items[start_idx:end_idx]
''',
            "tests/test_pagination.py": '''import pytest
from utils.pagination import paginate_items

def test_page_one_full_size():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = paginate_items(data, page=1, page_size=5)
    assert len(result) == 5
    assert result == [1, 2, 3, 4, 5]

def test_page_two():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = paginate_items(data, page=2, page_size=5)
    assert result == [6, 7, 8, 9, 10]
'''
        },
        "target_symbol": "paginate_items",
        "target_file": "utils/pagination.py"
    },
    {
        "id": "task_03_nested_key_error",
        "name": "KeyError in Nested Configuration Extractor",
        "description": "get_nested_config raises KeyError when intermediate keys are absent instead of returning fallback.",
        "files": {
            "config/extractor.py": '''"""Config extraction module."""
from typing import Dict, Any, Optional

def get_nested_config(config: Dict[str, Any], path: str, default: Optional[Any] = None) -> Any:
    """Traverse dot-separated path into dict, returning default if key missing."""
    keys = path.split(".")
    curr = config
    for key in keys:
        curr = curr[key]
    return curr
''',
            "tests/test_extractor.py": '''import pytest
from config.extractor import get_nested_config

def test_get_nested_found():
    cfg = {"database": {"host": "localhost", "port": 5432}}
    assert get_nested_config(cfg, "database.host") == "localhost"

def test_get_nested_missing_intermediate():
    cfg = {"database": {"port": 5432}}
    assert get_nested_config(cfg, "cache.redis.host", default="fallback") == "fallback"
'''
        },
        "target_symbol": "get_nested_config",
        "target_file": "config/extractor.py"
    },
    {
        "id": "task_04_upstream_caller_dependency",
        "name": "Data Transformer with Upstream Dependent Caller",
        "description": "format_user_summary must return a formatted dict with 'display_name' and 'is_active', but normalize_name trims whitespace incorrectly.",
        "files": {
            "services/user_service.py": '''"""User service with caller hierarchy."""

def normalize_name(raw_name: str) -> str:
    """Normalizes raw input username."""
    if not raw_name:
        return "Anonymous"
    return raw_name.strip().title()

def format_user_summary(user_data: dict) -> dict:
    """High-level summary consumed by API caller."""
    name = normalize_name(user_data.get("name", ""))
    active = bool(user_data.get("status") == "active")
    return {"display_name": name, "is_active": active}
''',
            "tests/test_user_service.py": '''import pytest
from services.user_service import format_user_summary, normalize_name

def test_normalize_empty():
    assert normalize_name("") == "Anonymous"
    assert normalize_name(None) == "Anonymous"

def test_format_user_summary():
    u = {"name": "  alice smith  ", "status": "active"}
    summary = format_user_summary(u)
    assert summary["display_name"] == "Alice Smith"
    assert summary["is_active"] is True
'''
        },
        "target_symbol": "normalize_name",
        "target_file": "services/user_service.py"
    }
]
