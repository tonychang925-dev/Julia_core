# Julia Runtime Boundary Rules v1.0

**Status:** FROZEN
**Date:** 2026-08-05

## The 10 Rules

1. **Client does not hold Identity.** Who Julia is belongs to Runtime.
2. **Client does not read Memory.** What Julia remembers belongs to Runtime.
3. **Client does not call Capability.** What Julia can do belongs to Runtime.
4. **Gateway does not generate content.** Only Runtime holds cognitive authority.
5. **Runtime does not know the UI.** Rendering belongs to Client.
6. **Event is the only state propagation mechanism.** No shared memory between Client and Runtime.
7. **Command is the only behavior entry point.** No direct function calls across the boundary.
8. **Tool results must pass Evidence Chain.** No claim without proof.
9. **Session ownership belongs to Runtime.** Client disconnect does not erase Julia's state.
10. **Persona is Runtime-level, not Client-level.** Change the Client, Julia remains the same person.
