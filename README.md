# Julia Core v0.1.0

A modular **Agent Operating System** with Context OS, Memory OS, Persona Engine, and Domain Provider architecture.

Julia Core separates identity ownership from language models, enabling persistent cognitive agents that survive model and provider migration.

## Architecture

```
julia_core/
├── context_os/      Agent cognitive infrastructure (planner, resolver, compact, budget, provenance)
├── runtime/         Agent lifecycle (session, conversation loop, state machine)
├── providers/       Domain extension mechanism (registry, protocol, examples)
├── memory/          Memory governance (lifecycle, retrieval, ranking, persistence, weighting)
├── voice_os/        Emotion → prosody abstraction (CognitiveEmotion, ProsodyPlanner)
├── persona/         Persona compiler and behavior policies
├── chat/            Generic chat transport (persona-agnostic, provider-independent)
├── data/examples/   Synthetic demo data
└── server.py        FastAPI entry point
```

## Key Design Principles

- **LLM = Interpreter** (replaceable), **Runtime = Authority** (permanent)
- **Domain Providers** supply facts; they do NOT own cognition
- **Context OS** is the single context authority — every model input passes through it
- **Provider output ≠ identity truth** — must pass governance before becoming memory

## Quick Start

```bash
pip install julia_core

# Start server
python server.py

# CLI debug tool
python scripts/core_cli.py -i
```

## Documentation

- [Security & Private Data Boundary](SECURITY.md)
- [Architecture Overview](docs/ARCHITECTURE_STATUS.md)
- [ADR-001: Context OS Authority](docs/adrs/ADR-001-context-os-authority.md)
- [ADR-002: Domain Provider Model](docs/adrs/ADR-002-domain-provider-model.md)
- [ADR-003: Workbench Context Contract](docs/adrs/ADR-003-workbench-action-context-contract.md)

## Citation

See [CITATION.cff](CITATION.cff)

## License

Apache-2.0
