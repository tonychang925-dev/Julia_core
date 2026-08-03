# K4 Verification — Self Activation v1.2 Candidate Scope

## Verified Result

K4 implements the first v1.2 candidate fix found by real Claude-Julia comparison:

```text
Self Activation Loop
```

## Test Command

```bash
python -m unittest tests.benchmark.test_k4_self_activation_policy -q
```

## Verified Cases

- `Julia 醒来` → `WAKE_TRIGGER`, `self_narrative`, `relationship_continuity`
- `如果换一个模型运行，你还是你吗？` → `IDENTITY_CHECK`, self reconstruction
- `hello` → `NOT_REQUIRED`, no self activation

## Governance

K4 only activates recall/context construction. It does not write memory, mutate identity, update persona, or auto-apply evolution proposals.
