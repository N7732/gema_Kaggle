"""
CodeGuardian Core Engine
Orchestrates the 5-stage SWE workflow:
1. Repository Reconnaissance
2. Bug Localization
3. Code Graph Reasoning
4. Minimal Patch Generation
5. Failure-Guided Recovery
"""

import os
import re
import time
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from agent.tools.repository_tools import (
    list_files, read_file_snippet, search_symbol, find_test_files, create_unified_diff
)
from agent.tools.graph_tools import build_code_graph, CodeGraph
from agent.tools.validation_tools import (
    run_pytest, validate_python_syntax, validate_patch_syntax, parse_traceback
)


class CodeGuardianAgent:
    """Autonomous Software Engineering Agent powered by Gemma 4."""

    def __init__(
        self,
        mode: str = "codeguardian_full",
        max_recovery_turns: int = 3,
        llm_client: Optional[Any] = None
    ):
        """
        Modes:
        - baseline: keyword localization, single patch attempt, no graph, no recovery
        - graph_guided: code graph localization and dependency checks, single patch attempt
        - codeguardian_full: code graph + minimal patch + iterative failure-guided recovery
        """
        self.mode = mode
        self.max_recovery_turns = max_recovery_turns if mode == "codeguardian_full" else 0
        self.llm_client = llm_client

    def solve_issue(
        self,
        repo_path: str,
        problem_statement: str,
        test_file: Optional[str] = None,
        patch_solver_func: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Runs the autonomous pipeline to diagnose, fix, and validate an issue."""
        start_time = time.time()
        trace: List[Dict[str, Any]] = []

        repo = Path(repo_path).resolve()
        if not repo.exists():
            return {
                "success": False,
                "error": f"Repository not found at {repo_path}",
                "trace": []
            }

        # -------------------------------------------------------------
        # STAGE 1: REPOSITORY RECONNAISSANCE
        # -------------------------------------------------------------
        all_py_files = list_files(str(repo), file_extensions=[".py"])
        candidate_tests = find_test_files(str(repo))
        selected_test = test_file if test_file else (candidate_tests[0] if candidate_tests else None)

        trace.append({
            "stage": "repository_recon",
            "files_found": len(all_py_files),
            "candidate_tests": candidate_tests[:5],
            "selected_test": selected_test
        })

        # -------------------------------------------------------------
        # STAGE 2: BUG LOCALIZATION & GRAPH REASONING
        # -------------------------------------------------------------
        code_graph = None
        graph_context = ""
        suspects: List[Dict[str, Any]] = []

        # Extract potential symbols/keywords from problem statement
        tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b", problem_statement)
        potential_symbols = [
            t for t in set(tokens)
            if t.lower() not in {"this", "that", "with", "from", "when", "then", "error", "issue", "expected", "actual", "test", "should"}
        ]

        if self.mode in ("graph_guided", "codeguardian_full"):
            code_graph = build_code_graph(str(repo), all_py_files)
            # Find symbols mentioned in graph
            matched_symbols = [sym for sym in potential_symbols if sym in code_graph.symbol_to_nodes]
            if not matched_symbols and potential_symbols:
                # Fallback to search_symbol
                for sym in potential_symbols[:5]:
                    matches = search_symbol(str(repo), sym)
                    if matches:
                        matched_symbols.append(sym)

            graph_context = code_graph.export_subgraph_context(matched_symbols[:5])
            trace.append({
                "stage": "code_graph_analysis",
                "nodes_count": len(code_graph.graph.nodes),
                "edges_count": len(code_graph.graph.edges),
                "matched_symbols": matched_symbols,
                "subgraph_summary": graph_context[:500]
            })

            # Rank suspects using graph definitions
            for sym in matched_symbols:
                dep_info = code_graph.query_symbol_dependencies(sym)
                for d in dep_info.get("definitions", []):
                    suspects.append({
                        "file": d["file"],
                        "line": d["lineno"],
                        "symbol": sym,
                        "callers_count": dep_info["total_callers"],
                        "callees_count": dep_info["total_callees"],
                        "confidence": 0.9 if d["file"] not in (selected_test or "") else 0.4
                    })
        else:
            # Baseline naive search
            for sym in potential_symbols[:3]:
                matches = search_symbol(str(repo), sym)
                for m in matches:
                    if not m["file"].startswith("test"):
                        suspects.append({
                            "file": m["file"],
                            "line": m["line_number"],
                            "symbol": sym,
                            "confidence": 0.6
                        })

        # Sort suspects by confidence
        suspects.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        target_suspect = suspects[0] if suspects else (
            {"file": all_py_files[0], "line": 1, "symbol": "unknown"} if all_py_files else None
        )

        trace.append({
            "stage": "bug_localization",
            "top_suspect": target_suspect,
            "suspects_count": len(suspects)
        })

        if not target_suspect:
            return {
                "success": False,
                "error": "Could not localize bug suspect.",
                "trace": trace
            }

        target_file = target_suspect["file"]
        target_full_path = repo / target_file
        if not target_full_path.exists():
            return {
                "success": False,
                "error": f"Target suspect file {target_file} does not exist.",
                "trace": trace
            }

        original_content = target_full_path.read_text(encoding="utf-8", errors="replace")

        # -------------------------------------------------------------
        # STAGE 3 & 4 & 5: PATCH GENERATION, VALIDATION & RECOVERY LOOP
        # -------------------------------------------------------------
        final_patch = ""
        resolved = False
        turns_used = 0
        last_failure_info = None

        # Initial baseline test check to verify failure state
        pre_test_run = run_pytest(str(repo), selected_test)
        initial_test_passed = pre_test_run["success"]

        max_attempts = 1 + self.max_recovery_turns

        for turn in range(max_attempts):
            turns_used = turn + 1
            stage_name = "minimal_patch_generation" if turn == 0 else f"failure_guided_recovery_turn_{turn}"

            # Synthesize patch candidate
            if patch_solver_func:
                candidate_content = patch_solver_func(
                    original_content=original_content,
                    problem_statement=problem_statement,
                    graph_context=graph_context,
                    failure_info=last_failure_info,
                    turn=turn
                )
            elif self.llm_client:
                candidate_content = self._call_llm_solver(
                    original_content=original_content,
                    problem_statement=problem_statement,
                    graph_context=graph_context,
                    failure_info=last_failure_info,
                    turn=turn
                )
            else:
                candidate_content = original_content

            # Syntax validation of modified code
            syntax_check = validate_python_syntax(candidate_content, filename=target_file)
            if not syntax_check["valid"]:
                last_failure_info = {
                    "has_failures": True,
                    "exception_type": "SyntaxError",
                    "exception_message": syntax_check["error"],
                    "traceback_snippet": f"SyntaxError at line {syntax_check.get('line')}: {syntax_check.get('error')}"
                }
                trace.append({
                    "stage": stage_name,
                    "turn": turn,
                    "syntax_valid": False,
                    "error": syntax_check["error"]
                })
                continue

            # Generate unified diff
            patch_diff = create_unified_diff(original_content, candidate_content, target_file)
            diff_syntax = validate_patch_syntax(patch_diff)

            # Apply candidate code to repository temporarily
            target_full_path.write_text(candidate_content, encoding="utf-8")

            # Validate by running test suite
            test_res = run_pytest(str(repo), selected_test)

            if test_res["success"]:
                # Success! All tests passed
                resolved = True
                final_patch = patch_diff
                trace.append({
                    "stage": stage_name,
                    "turn": turn,
                    "test_passed": True,
                    "output": test_res["output"][:300],
                    "patch_diff": patch_diff
                })
                break
            else:
                # Failure: capture traceback and diagnostic info for recovery
                last_failure_info = test_res["diagnostics"]
                trace.append({
                    "stage": stage_name,
                    "turn": turn,
                    "test_passed": False,
                    "exception": last_failure_info.get("exception_type"),
                    "traceback_snippet": last_failure_info.get("traceback_snippet", "")[:400]
                })

        # Revert file to original state if not resolved, or leave clean patch artifact
        if not resolved:
            target_full_path.write_text(original_content, encoding="utf-8")
        else:
            # Revert repository to clean state, keeping patch diff as the submission artifact
            target_full_path.write_text(original_content, encoding="utf-8")

        elapsed_time = time.time() - start_time
        lines_changed = len([line for line in final_patch.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))])

        return {
            "success": resolved,
            "patch": final_patch,
            "turns_used": turns_used,
            "mode": self.mode,
            "elapsed_seconds": round(elapsed_time, 2),
            "lines_changed": lines_changed,
            "initial_test_passed": initial_test_passed,
            "trace": trace
        }

    def _call_llm_solver(self, original_content: str, problem_statement: str, graph_context: str, failure_info: Optional[Dict], turn: int) -> str:
        """Invokes LLM interface if configured."""
        if hasattr(self.llm_client, "generate_patch"):
            return self.llm_client.generate_patch(
                original_content=original_content,
                problem_statement=problem_statement,
                graph_context=graph_context,
                failure_info=failure_info
            )
        return original_content
