# Minimal Patch Generation & Failure Recovery Prompt

You are performing Stage 4 and Stage 5 of CodeGuardian: **Minimal Patch Generation and Failure-Guided Recovery**.

## Input
- **Target File**: {{TARGET_FILE}}
- **Original Source Snippet**:
```python
{{ORIGINAL_CODE}}
```

- **Callers & Dependent Functions (Graph Context)**:
{{DEPENDENCY_CONTEXT}}

- **Validation Error / Traceback (if in recovery turn)**:
{{FAILURE_TRACEBACK}}

- **Prior Attempt (if any)**:
{{PREVIOUS_PATCH}}

## Constraints
1. Edit only the target block. Do not rewrite functions unnecessarily.
2. Ensure backward compatibility: callers listed in the dependency graph must not break.
3. Handle corner cases (e.g., None checks, type mismatches, boundary indices).
4. If this is a recovery turn, address the specific assertion failure or exception reported in the traceback.

## Output Structure
Respond in valid JSON:
```json
{
  "diagnosis": "Analysis of the failure or fix requirements",
  "root_cause_confirmed": true,
  "modified_code": "The complete replacement content for the target snippet",
  "explanation": "Why this minimal change fixes the issue without regressions"
}
```
