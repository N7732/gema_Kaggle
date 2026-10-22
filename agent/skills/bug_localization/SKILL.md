---
name: bug_localization
description: Isolate the precise module, class, function, or line block causing a reported issue using heuristic and semantic search.
---

# Bug Localization Skill

## Purpose
Pinpoint the exact location of defects from bug report text, error stack traces, and symbol mentions.

## Strategy
1. **Traceback Extraction**: If the issue includes a traceback, prioritize the lowest application frame.
2. **Entity Recognition**: Extract referenced class names, function names, and exception types.
3. **Symbol Search**: Run exact regex or symbol index search across the repository.
4. **Rank Candidates**: Rank localized suspects by confidence score (0.0 to 1.0).
