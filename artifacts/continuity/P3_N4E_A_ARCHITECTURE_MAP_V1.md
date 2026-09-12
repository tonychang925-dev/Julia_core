# P3 N4E-A Architecture Authority Map

## ARCHITECTURE_AUTHORITY_MAP

- Identity authority owns `IdentityVersion` admission, supersession, retirement, and lineage selection.
- MemoryExperience authority owns `MemoryExperienceRecord` admission, supersession, retirement, and lineage selection.
- RuntimeCanonicalAuthorityBinding authority owns runtime binding admission, supersession, retirement, and lineage selection.
- N4E-A persistence owns byte-neutral envelope representation, deterministic digests, integrity validation, exact restoration, and fail-closed behavior only.

## PERSISTED_OBJECT_MAP

- Identity envelope: exact governed `IdentityVersion`, exact `IdentityRef`, complete governance history, terminal status, lineage, provenance, and object schema.
- MemoryExperience envelope: exact governed `MemoryExperienceRecord`, exact `MemoryExperienceRef`, complete admission history, terminal status, lineage, provenance, and object schema.
- RuntimeBinding envelope: exact governed `RuntimeCanonicalAuthorityBinding`, exact `RuntimeCanonicalAuthorityBindingRef`, complete governance history, terminal status, lineage, provenance, and object schema.

## GOVERNANCE_EVENT_MAP

- Existing event identifier, target ref, lifecycle status, actor, reason, timestamp, and ordering are copied exactly.
- The reconstruction seam never invokes `store_candidate`, `admit`, `supersede`, or `retire`.
- The reconstruction seam never synthesizes or repairs event content.

## COLD_LOAD_RECONSTRUCTION_MAP

1. Read exact durable envelope through a family-qualified reader.
2. Reject unknown, partial, malformed, unsupported, or non-canonical envelope structure.
3. Verify payload digest and envelope digest before semantic parsing.
4. Parse only the exact schema declared for the declared authority family.
5. Verify family, ref, object schema, event targets, lifecycle history, lineage/predecessor closure, provenance, and terminal state.
6. Restore the immutable governed object into a repository snapshot without lifecycle mutation.
7. Resolve only by exact reference thereafter.

## ADAPTER_BOUNDARY_MAP

- `DurableAuthorityReader.read_exact(family, ref)` returns one already-validated exact durable envelope or fails closed.
- `DurableAuthorityWriter.write_exact(envelope)` persists one immutable envelope or fails closed.
- Optional `list_exact_refs(family)` is persistence mechanics only and is never selection.
- The production physical adapter is intentionally unspecified.

## FORBIDDEN_BEHAVIOR_MAP

- Forbidden: storage selection, production wiring, production writes, legacy migration, Golden Mira admission, alias resolution, latest/default/current discovery, semantic repair, synthetic refs, synthetic events, digest generation during load, cross-family coercion, and best-effort continuation.
- Loading is not admission, recovery is not selection, bootstrap is not canonicalization, and storage is not authority.

## IMPLEMENTATION_PLAN

1. Define the immutable envelope, family schemas, deterministic canonical JSON, digest laws, and fail-closed error taxonomy.
2. Add exact parsers for the three governed object families.
3. Add read/write adapter protocols and an exact restoration API that imports governed snapshots into repositories.
4. Add synthetic candidate-only positive and negative tests.
5. Add the required evidence artifact and run bounded static/regression checks.
