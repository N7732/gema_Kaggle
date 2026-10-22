"""
Unit tests for code graph analysis tools.
"""

import tempfile
from pathlib import Path
from agent.tools.graph_tools import build_code_graph, CodeGraph

def test_code_graph_ast_and_calls():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        code = '''
def helper(x):
    return x * 2

def main():
    return helper(5)
'''
        (tmp / "sample.py").write_text(code, encoding="utf-8")

        graph = build_code_graph(str(tmp), ["sample.py"])

        assert "helper" in graph.symbol_to_nodes
        assert "main" in graph.symbol_to_nodes

        dep_info = graph.query_symbol_dependencies("helper")
        assert dep_info["total_callers"] >= 1
        assert any("main" in caller for caller in dep_info["callers"])

def test_code_graph_shortest_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        code = '''
def step_a():
    return step_b()

def step_b():
    return 42
'''
        (tmp / "pipeline.py").write_text(code, encoding="utf-8")
        graph = build_code_graph(str(tmp), ["pipeline.py"])

        path = graph.find_shortest_dependency_path("step_a", "step_b")
        assert path is not None
        assert len(path) == 2
