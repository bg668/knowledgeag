# Repository Instructions

## Project working style

When changing this repository:

- Read the existing layout before proposing changes.
- Reuse existing modules before creating new ones.
- Keep changes minimal and localized.
- Preserve public interfaces unless the plan explicitly justifies changing them.
- Prefer a small runnable implementation over a complete framework.
- Add or update tests when behavior changes.
- If tests are unavailable, provide a clear manual verification command or scenario.

## Architecture planning rule

For any change involving architecture, module boundaries, providers, agent runtime, CLI/TUI structure, workflow, storage, or design-pattern choices:

1. Use Plan mode.
2. Apply the $minimal-architecture-plan skill.
3. Produce a plan with:
   - goal
   - smallest runnable loop
   - files to change
   - module boundaries
   - design pattern decisions
   - do / do not
   - development order
   - verification method

## Module boundary rule

When proposing a new module, describe:

- Responsibility
- Non-responsibility
- Public interface
- Dependencies
- Verification method

## Do not

- Do not rewrite the whole project when a localized change is enough.
- Do not introduce a plugin system before there are at least two real implementations.
- Do not add abstract base classes unless the interface is stable and used by more than one implementation.
- Do not add global singletons for config, LLM clients, stores, or runtime objects.
- Do not mix UI logic, agent runtime logic, provider calls, and storage logic in the same module.