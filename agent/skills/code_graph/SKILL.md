---
name: code_graph
description: Construct and query Python AST call graphs, dependency paths, and caller/callee networks with NetworkX.
---

# Code Graph Skill

## Purpose
Prevent collateral breakages and regression errors by analyzing the caller-callee and import dependency network around localized bug suspects.

## Implementation Details
1. **AST Parsing**: Parse Python source trees using `ast.parse`.
2. **Graph Modeling**: Build a directed multi-graph where:
   - Nodes represent files, classes, and functions with attributes (`file`, `type`, `lineno`, `name`).
   - Edges represent `CALLS`, `IMPORTS`, or `DEFINES`.
3. **Impact Analysis**: Query upstream dependents (callers) and downstream prerequisites (callees) before modifying any target function.
4. **Context Injection**: Provide the LLM with immediate upstream and downstream nodes so patch generation is context-aware.
