# Security Policy — Private Data Boundary

## Public vs Private

`julia_core` is a **public, reusable Agent Operating System**. It must NOT contain any real identity, memory, or personal data.

### Never in julia_core

- Personal identity profiles (real names, relationships, locations)
- Conversation history or transcripts
- Private embeddings or fine-tuned weights
- User preferences or behavioral data
- Any data traceable to a specific person

### Always in julia_core

- Architecture, code, tests, schemas, examples
- Synthetic demo data (`data/examples/`)
- Public API contracts

### Private data belongs in a separate private repository

```
julia_private/          ← private, not open source
    ├── identity/       ← real persona profiles
    ├── memory/         ← real conversations
    └── preferences/    ← user preferences

julia_core/             ← public, open source
    ├── context_os/     ← cognitive engine
    ├── runtime/        ← agent lifecycle
    ├── providers/      ← domain plugins
    └── data/examples/  ← synthetic demo data only
```
