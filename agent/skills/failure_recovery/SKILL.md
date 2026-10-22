---
name: failure_recovery
description: Failure-guided iterative recovery loop utilizing test execution tracebacks to correct patch mistakes.
---

# Failure-Guided Recovery Skill

## Purpose
Turn failing validation tests into high-fidelity diagnostic signals for automatic patch refinement without human intervention.

## Recovery Protocol
1. **Execute Candidate**: Apply generated patch dry-run in test environment and run target test suite.
2. **Success Check**: If all tests pass (0 failures, 0 errors), approve patch for final submission.
3. **Traceback Analysis**:
   - Extract `AssertionError`, `TypeError`, `KeyError`, etc.
   - Extract failing test name and failure line number.
   - Extract actual vs expected diff from pytest output.
4. **Hypothesis Revision**: Identify what assumption in the first patch was incorrect.
5. **Re-synthesis**: Prompt model with the original context, the failed patch, and the traceback explanation to produce a refined minimal patch.
6. **Limit Turns**: Limit iterative recovery to `max_recovery_turns` (default: 3) to prevent infinite loops.
