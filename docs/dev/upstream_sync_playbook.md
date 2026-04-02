# Upstream Sync Playbook

This repository tracks upstream MUIO releases. For sync work such as the v5.5 stack in [#388](https://github.com/EAPD-DRB/MUIOGO/issues/388), follow upstream by default and only diverge when MUIOGO needs portability, security, runtime reliability, or downstream integration fixes.

## Sync Order

Land the v5.5 stack in this order:

1. [#389](https://github.com/EAPD-DRB/MUIOGO/issues/389): guardrails and smoke harness. This PR is the gate.
2. Backend and runtime safe changes from the remaining [#388](https://github.com/EAPD-DRB/MUIOGO/issues/388) child work.
3. Diagnostics UI follow-up work.
4. Result metadata bundle follow-up work, including `Variables.json` and rendering alignment.

Use [#390](https://github.com/EAPD-DRB/MUIOGO/issues/390) as the overlap inventory before resolving conflicts or choosing a deliberate downstream divergence.

## Protected Overlap Surface

Review these files carefully in every upstream sync PR because they are the highest-overlap backend/runtime touch points:

- `API/Classes/Base/Config.py`
- `API/Classes/Base/FileClass.py`
- `API/Classes/Case/DataFileClass.py`
- `API/Classes/Case/OsemosysClass.py`
- `API/Routes/DataFile/DataFileRoute.py`
- `API/app.py`

If a PR touches any of them, state whether the change follows upstream as-is or intentionally diverges and why.

## Rejected Upstream Patterns

Do not land these patterns without an explicit maintainer decision:

- writing logs under `WebAPP/`, including `WebAPP/app.log`
- deleting logs on startup
- current-working-directory-relative paths for important I/O
- `shell=True` subprocess usage
- compact JSON as the default write format
- `FileClassCompressed.py`
- similar compression or logging rewrites that reduce portability or make runtime behavior harder to reason about

## Clean-Base Verification

Before starting an upstream merge, after resolving conflicts, and before requesting review, run:

```bash
python scripts/verify_clean_base.py
```

This command checks:

- unresolved git operation state from `.git` control files such as `MERGE_HEAD` and rebase markers
- conflict markers in common tracked text files
- Python source compilation without assuming the repo root is writable
- stdlib `unittest` smoke coverage for app import and fixed routes

Fix every reported failure before continuing with the sync.

## Validation Scope For PR 1

For [#389](https://github.com/EAPD-DRB/MUIOGO/issues/389), keep validation intentionally small:

- run `python scripts/verify_clean_base.py`
- confirm the smoke harness passes on a supported Python interpreter

The CBC demo and broader backend/runtime validation belong to later PRs in the [#388](https://github.com/EAPD-DRB/MUIOGO/issues/388) stack, not this guardrail PR.
