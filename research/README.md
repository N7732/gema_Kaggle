# CodeGuardian Research & Evaluation Framework

This directory houses the experimental setup, benchmark runners, ablation studies, and evaluation reporting for the **CodeGuardian** Kaggle agent.

## Experimental Variants

1. **Baseline Agent (`variant_a`)**:
   - Issue analysis + naive file retrieval.
   - One-shot patch generation using Gemma 4.
   - No structured AST call graph, no automatic test recovery loop.

2. **Graph-Guided Agent (`variant_b`)**:
   - Issue analysis + NetworkX AST & Call-Graph root cause localization.
   - Context injection prioritized by graph centrality and symbol callers/callees.
   - One-shot minimal patch generation.

3. **CodeGuardian Full (`variant_c`)**:
   - Graph-Guided reasoning and AST call-graph localization.
   - Strict minimal patch generation constraint (editing only relevant blocks).
   - Dynamic test execution in environment.
   - Multi-turn failure-guided recovery loop (parsing traceback, hypothesis update, targeted re-patching).

## Evaluation Metrics
- **Localization Accuracy (Top-1 / Top-3)**: Ratio of instances where the faulty file/symbol is in the agent's target edit plan.
- **Syntactic Validity**: Percentage of generated patches that are valid unified diffs without syntax errors.
- **Pass@1 Rate (Resolved Ratio)**: Percentage of benchmark instances where generated patches pass all failing unit tests without regressing passing tests.
- **Patch Minimality**: Mean line delta (`added + deleted`) compared to ground truth patch.
- **Recovery Efficiency**: Success rate of multi-turn repair attempts after initial validation failure.
