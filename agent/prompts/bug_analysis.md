# Bug Analysis & Localization Prompt

You are performing Stage 1 and Stage 2 of CodeGuardian: **Repository Reconnaissance & Bug Localization**.

## Input
- **Issue Description / Problem Statement**:
{{PROBLEM_STATEMENT}}

- **Repository Tree Context**:
{{REPO_STRUCTURE}}

- **Extracted Code Graph Subgraph**:
{{GRAPH_CONTEXT}}

## Instructions
1. **Symptom Extraction**: Identify the expected behavior vs. actual behavior described in the issue.
2. **Defect Hypothesis**: Formulate 1-2 hypotheses explaining the discrepancy.
3. **Suspect Ranking**:
   - List the candidate files and symbols (functions/classes) ranked by probability of containing the defect.
   - For each suspect, explain why the code graph links it to the reported symptom.
4. **Validation Test Candidate**: Identify or specify the minimal test case needed to trigger the bug.

## Output Structure
Respond in valid JSON:
```json
{
  "problem_summary": "Short summary of the bug",
  "expected_behavior": "What should happen",
  "actual_behavior": "What is happening",
  "suspect_files": [
    {
      "path": "path/to/suspect.py",
      "symbol": "function_or_class_name",
      "confidence": 0.95,
      "reasoning": "Reason based on traceback and call-graph"
    }
  ],
  "reproduction_strategy": "Command or test function to reproduce"
}
```
