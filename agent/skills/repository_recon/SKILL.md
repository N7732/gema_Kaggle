---
name: repository_recon
description: Autonomous exploration of repository structure, identifying entry points, relevant modules, and test suites.
---

# Repository Reconnaissance Skill

## Purpose
Quickly map an unknown codebase to locate relevant modules and reproduction test files without loading entire repos into LLM context.

## Workflow
1. List file trees filtering out virtualenvs, git directories, caches, and binaries.
2. Locate package root, configuration files (`pyproject.toml`, `setup.cfg`, `requirements.txt`).
3. Locate test directories (`tests/`, `testing/`, `*_test.py`).
4. Identify candidate modules corresponding to the keywords extracted from the problem statement.
