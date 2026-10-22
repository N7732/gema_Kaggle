"""
End-to-end tests for the CodeGuardian agent engine.
"""

import tempfile
from pathlib import Path
from agent.engine import CodeGuardianAgent

def test_codeguardian_engine_autonomous_recovery():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "math_mod.py").write_text('''def multiply(a, b):
    # Bug: returns addition
    return a + b
''', encoding="utf-8")

        (tmp / "tests").mkdir()
        (tmp / "tests" / "test_math.py").write_text('''from math_mod import multiply

def test_multiply():
    assert multiply(3, 4) == 12
''', encoding="utf-8")

        def recovery_solver(original_content, problem_statement, graph_context, failure_info, turn):
            if turn == 0:
                # First turn fails deliberately
                return original_content.replace("return a + b", "return a + 0")
            # Recovery turn fixes properly
            return original_content.replace("return a + b", "return a * b")

        agent = CodeGuardianAgent(mode="codeguardian_full", max_recovery_turns=2)
        result = agent.solve_issue(
            repo_path=str(tmp),
            problem_statement="multiply returns incorrect addition result",
            test_file="tests/test_math.py",
            patch_solver_func=recovery_solver
        )

        assert result["success"] is True
        assert result["turns_used"] == 2
        assert "--- a/math_mod.py" in result["patch"]
        assert "+    return a * b" in result["patch"]
