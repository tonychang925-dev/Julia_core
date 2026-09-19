# Prompt Construction

`run_jic_r0.py` builds each request as:

1. the fixed generic reasoning shell;
2. the case's fixed question;
3. the case's immutable `evidence_snapshot` and source identity;
4. condition A adds nothing;
5. condition B appends the exact raw JSON at the pinned Strategy Card SHA;
6. condition C appends the exact Markdown at the pinned GIC SHA.

Condition names, expected outcomes, evaluator mappings, and replay assertions are never included in model input.
