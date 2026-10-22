# CodeGuardian Dataset Architecture

This directory contains data structures, benchmark manifests, and working directories for evaluating and benchmarking CodeGuardian against software engineering challenges (e.g. SWE-bench, Defects4J, Kaggle Gemma Developer Agent tasks).

## Directory Structure
- `raw/`: Original, unmodified datasets or authorized benchmark exports (e.g., SWE-bench lite, Kaggle developer benchmark tasks).
- `interim/`: Intermediate artifacts produced during tokenization, AST extraction, or repository cloning.
- `processed/`: Validated, normalized task records ready for evaluation and benchmark replay.
- `external/`: Additional licensed reference repositories or documentation corpus.
- `splits/`: Train, validation, and test split manifests.
- `manifests/`: Dataset metadata, schema definitions, version hashes, and compliance manifests.

## Evaluation & Benchmark Protocol
Per competition guidelines:
1. Benchmark tasks are evaluated in isolated sandboxes.
2. No data leakage between train/test splits.
3. Every sample must record: `issue_id`, `repo_name`, `base_commit`, `problem_statement`, `test_patch`, `hints_text`.
