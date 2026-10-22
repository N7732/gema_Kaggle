"""
Code Graph Analysis Tools for CodeGuardian Agent.
Constructs AST dependency graphs, call hierarchies, and impact subgraphs using NetworkX.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import networkx as nx

class ASTGraphVisitor(ast.NodeVisitor):
    """AST Visitor that extracts functions, classes, calls, imports, and inheritance."""

    def __init__(self, file_path: str):
        self.file_path = file_path.replace("\\", "/")
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.definitions: List[Dict[str, Any]] = []
        self.calls: List[Tuple[str, str, int]] = []
        self.imports: List[Dict[str, Any]] = []
        self.inheritances: List[Tuple[str, str]] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "asname": alias.asname or alias.name,
                "lineno": node.lineno
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            self.imports.append({
                "module": f"{mod}.{alias.name}" if mod else alias.name,
                "name": alias.name,
                "asname": alias.asname or alias.name,
                "lineno": node.lineno
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self.current_class
        class_name = node.name
        self.current_class = class_name

        self.definitions.append({
            "type": "class",
            "name": class_name,
            "qualified_name": f"{self.file_path}::{class_name}",
            "file": self.file_path,
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", node.lineno)
        })

        for base in node.bases:
            if isinstance(base, ast.Name):
                self.inheritances.append((class_name, base.id))
            elif isinstance(base, ast.Attribute):
                self.inheritances.append((class_name, base.attr))

        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node)

    def _handle_function(self, node: Any):
        prev_function = self.current_function
        func_name = node.name
        qualified_name = (
            f"{self.file_path}::{self.current_class}::{func_name}"
            if self.current_class
            else f"{self.file_path}::{func_name}"
        )
        self.current_function = qualified_name

        self.definitions.append({
            "type": "method" if self.current_class else "function",
            "name": func_name,
            "qualified_name": qualified_name,
            "class": self.current_class,
            "file": self.file_path,
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", node.lineno),
            "args": [arg.arg for arg in node.args.args]
        })

        self.generic_visit(node)
        self.current_function = prev_function

    def visit_Call(self, node: ast.Call):
        callee_name = None
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr

        if callee_name and self.current_function:
            self.calls.append((self.current_function, callee_name, node.lineno))

        self.generic_visit(node)


class CodeGraph:
    """Directed graph capturing semantic relationships between codebase components."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.symbol_to_nodes: Dict[str, Set[str]] = {}

    def build_from_files(self, repo_path: str, files: List[str]) -> "CodeGraph":
        """Builds code graph across the specified python files."""
        repo = Path(repo_path)
        for rel_file in files:
            full_path = repo / rel_file
            if not full_path.is_file() or not rel_file.endswith(".py"):
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                tree = ast.parse(content, filename=rel_file)
            except (SyntaxError, UnicodeDecodeError):
                continue

            visitor = ASTGraphVisitor(rel_file)
            visitor.visit(tree)

            # File node
            self.graph.add_node(rel_file, type="module", file=rel_file)

            # Definitions
            for item in visitor.definitions:
                qname = item["qualified_name"]
                name = item["name"]
                self.graph.add_node(
                    qname,
                    type=item["type"],
                    name=name,
                    file=item["file"],
                    lineno=item["lineno"],
                    end_lineno=item["end_lineno"]
                )
                self.graph.add_edge(rel_file, qname, relation="DEFINES")

                if name not in self.symbol_to_nodes:
                    self.symbol_to_nodes[name] = set()
                self.symbol_to_nodes[name].add(qname)

            # Inheritances
            for subclass, base in visitor.inheritances:
                sub_q = f"{rel_file}::{subclass}"
                self.graph.add_edge(sub_q, base, relation="INHERITS")

            # Calls
            for caller_q, callee_name, lineno in visitor.calls:
                target_candidates = self.symbol_to_nodes.get(callee_name, set())
                if target_candidates:
                    for target_q in target_candidates:
                        self.graph.add_edge(caller_q, target_q, relation="CALLS", lineno=lineno)
                else:
                    self.graph.add_node(callee_name, type="external_or_unresolved", name=callee_name)
                    self.graph.add_edge(caller_q, callee_name, relation="CALLS", lineno=lineno)

        return self

    def query_symbol_dependencies(self, symbol_name: str, depth: int = 1) -> Dict[str, Any]:
        """Queries upstream callers (impact) and downstream callees (dependencies)."""
        matching_nodes = self.symbol_to_nodes.get(symbol_name, set())
        if not matching_nodes:
            # check direct node match
            matching_nodes = {n for n in self.graph.nodes if symbol_name in n}

        callers = set()
        callees = set()
        definitions = []

        for node in matching_nodes:
            if node in self.graph:
                node_data = self.graph.nodes[node]
                definitions.append({
                    "qualified_name": node,
                    "file": node_data.get("file"),
                    "lineno": node_data.get("lineno"),
                    "type": node_data.get("type")
                })
                # Upstream (predecessors calling this node)
                for pred in self.graph.predecessors(node):
                    edge_data = self.graph.get_edge_data(pred, node, {})
                    if edge_data.get("relation") == "CALLS":
                        callers.add(pred)

                # Downstream (successors called by this node)
                for succ in self.graph.successors(node):
                    edge_data = self.graph.get_edge_data(node, succ, {})
                    if edge_data.get("relation") == "CALLS":
                        callees.add(succ)

        return {
            "symbol": symbol_name,
            "definitions": definitions,
            "callers": sorted(list(callers)),
            "callees": sorted(list(callees)),
            "total_callers": len(callers),
            "total_callees": len(callees)
        }

    def find_shortest_dependency_path(self, source_symbol: str, target_symbol: str) -> Optional[List[str]]:
        """Finds shortest invocation or dependency path between two symbols."""
        source_nodes = self.symbol_to_nodes.get(source_symbol, {source_symbol})
        target_nodes = self.symbol_to_nodes.get(target_symbol, {target_symbol})

        for s in source_nodes:
            for t in target_nodes:
                if s in self.graph and t in self.graph:
                    try:
                        return nx.shortest_path(self.graph, source=s, target=t)
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        continue
        return None

    def export_subgraph_context(self, suspect_symbols: List[str]) -> str:
        """Formats subgraphs for prompt injection to provide graph-guided reasoning context."""
        lines = []
        for sym in suspect_symbols:
            info = self.query_symbol_dependencies(sym)
            lines.append(f"### Symbol: {sym}")
            if info["definitions"]:
                for d in info["definitions"]:
                    lines.append(f"  - Defined in {d['file']} at line {d['lineno']} ({d['type']})")
            if info["callers"]:
                lines.append(f"  - Callers (Impact Risk): {', '.join(info['callers'][:5])}")
            if info["callees"]:
                lines.append(f"  - Callees (Dependencies): {', '.join(info['callees'][:5])}")
            lines.append("")
        return "\n".join(lines)


def build_code_graph(repo_path: str, files: Optional[List[str]] = None) -> CodeGraph:
    """Convenience helper to construct and return a CodeGraph instance."""
    from agent.tools.repository_tools import list_files
    if files is None:
        files = list_files(repo_path, file_extensions=[".py"])
    graph = CodeGraph()
    return graph.build_from_files(repo_path, files)
