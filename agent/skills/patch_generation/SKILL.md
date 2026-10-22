---
name: patch_generation
description: Synthesize minimal, syntactically verified unified diffs targeting only the defective block.
---

# Minimal Patch Generation Skill

## Purpose
Generate focused, high-precision code fixes that maximize competition pass rates while keeping line deltas strictly minimal.

## Rules
1. **Never Reformat**: Do not touch indentation, line breaks, or docstrings outside the target bug fix.
2. **Minimal Edit Window**: Replace only the smallest block of code necessary.
3. **Format Integrity**: Generate valid unified diff headers (`--- a/...`, `+++ b/...`, `@@ -start,len +start,len @@`).
4. **Syntax Verification**: Verify Python syntax with `compile(code, filename, 'exec')` prior to test evaluation.
