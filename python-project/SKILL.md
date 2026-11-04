---
name: python-project
description: >-
  Initialize a new Python project, adopt an existing one, or review a project
  against an opinionated baseline: uv for environments and dependencies, ruff for
  lint, format, and structural limits, pytest with 90% coverage on new code,
  basedpyright type checking at one of four modes, vulture dead-code checks,
  pre-commit, Poe the Poet tasks, VS Code settings, and a CONTRIBUTING.md of
  Python conventions. Use whenever someone wants to scaffold, bootstrap,
  standardize, or migrate a Python project (pip, requirements.txt, poetry,
  hatch), set up or fix uv/ruff/pytest/pyright/basedpyright/coverage config,
  raise or lower a project's type-checking strictness, or audit whether a repo
  follows these Python conventions, even when they name only one of the tools.
compatibility: Requires uv and git. devbox is optional; it supplies uv.
---

# Python project baseline

Set up, migrate, or review a Python project against one baseline. Pick the mode, then read its file in `references/` and follow it:

| Mode | When | Steps |
| --- | --- | --- |
| **Init** | An empty directory, or one with no `pyproject.toml`. Scaffold it. | [init.md](references/init.md) |
| **Adopt** | An existing project on another toolchain (pip and `requirements.txt`, poetry, hatch, setuptools). Move it onto uv and the baseline. | [adopt.md](references/adopt.md) |
| **Review** | An existing uv-managed project. Report drift from the baseline in its config, files, and layout, and stop. Apply changes only after the user approves them. | [review-project.md](references/review-project.md) |
| **Code review** | A request to review a project's code. Report where the code breaks the conventions in `references/python.md`, and stop. Apply changes only after the user approves them. | [review-code.md](references/review-code.md) |

Changing an existing project's typing mode follows [typing-mode.md](references/typing-mode.md).

Adopt also starts with a review: report first, then change what was approved. Never overwrite a project's README prose, `AGENTS.md` architecture notes, or project-specific config to match a template. Merge into them.

`<SKILL_DIR>` below means this skill's directory.

## What the baseline contains

| Project file | Source in this skill | How it gets there |
| --- | --- | --- |
| `pyproject.toml` `[tool.*]` tables | `assets/pyproject/tool.*.toml`, picked by `assets/pyproject/toolsets.toml` | `sync-pyproject` (below) |
| `CONTRIBUTING.md` | `references/python.md` | Copy without its frontmatter |
| `AGENTS.md` | `assets/AGENTS.template.md` | Fill in; merge into an existing one |
| `CLAUDE.md` | `assets/CLAUDE.md` | Copy (`@AGENTS.md`) unless one exists |
| `README.md` | `assets/README.template.md` | Fill in; merge into an existing one |
| `.pre-commit-config.yaml` | `assets/pre-commit-config.yaml` | Copy; merge into existing |
| `devbox.json` | `assets/devbox.json` | Copy; set the `run` script. Each other script wraps `uv run poe <task>` |
| `.vscode/settings.json`, `.vscode/extensions.json` | `assets/vscode/` | Copy; merge into existing |
| `.gitignore` | `assets/.gitignore-template` | Append missing lines |
| `tests/conftest.py` | `assets/tests/conftest.py` | Copy unless one exists |
| `scripts/check_file_length.py`, `scripts/changed_lines_coverage.py` | `assets/scripts/` | Copy |

Unless the user directs otherwise, use the existing `.agents/` or `.claude/` directories for your own working files (e.g. test fixtures, run output, memory files, etc.) within the project. If they do not exist, ask the user where your managed files should go.

uv enforces `[tool.uv] required-version` on every command. devbox supplies uv as a package in `devbox.json`. Keep that pin on the newest uv devbox offers (`devbox search uv`): pin it when creating `devbox.json`, and in Review report a newer one as drift. Upgrade only with the user's approval. Without devbox, install uv from https://docs.astral.sh/uv/getting-started/installation/.

The project layout is `src/<package>/` with a top-level `tests/` and no `__init__.py` files under `tests/`. The build backend is `uv_build`.

## Sync pyproject.toml using the included script

The `sync-pyproject` command should be used for every `[tool.*]` table. Do not hand-copy the fragments: the script merges them into an existing file, keeps its comments, and applies the typing mode consistently across basedpyright, ruff, and any optional checker.

The command ships in this skill's own package (`<SKILL_DIR>/pyproject.toml`). The first `uv run --project <SKILL_DIR>` builds `<SKILL_DIR>/.venv` from `<SKILL_DIR>/uv.lock`; later runs reuse it. `--project <SKILL_DIR>` picks the environment only. It does not change the working directory, so the trailing `--project .` still names the target project.

```bash
uv run --project <SKILL_DIR> sync-pyproject --project .            # report only
uv run --project <SKILL_DIR> sync-pyproject --project . --write    # apply
```

Options: `--typing-mode off|basic|standard|strict` (default: the project's current `[tool.basedpyright] typeCheckingMode`, else `standard`), and `--with ty` or `--with pyrefly` to configure an optional checker. A checker the project already configures is detected.

Report lines and what to do with them:

| Kind | Meaning | `--write` |
| --- | --- | --- |
| `MISSING` | Baseline key absent | Adds it |
| `DIFFERS` | Key holds another value | Sets the baseline value |
| `OBSOLETE` | Superseded key, e.g. `tool.ruff.target-version` | Removes it |
| `CONFLICT` | Settings for a tool the baseline replaces, e.g. `tool.pyright`, `tool.black`, `tool.pytest.ini_options` | No. Move the settings as the line says, then delete the old table |
| `EXTRA` | Key or rule-list entry the typing mode forbids | Removes it |
| `RELAXED` | Ignore entry the project added; does not fail the check | No. Confirm it is deliberate and recorded in `AGENTS.md` |
| `DEPENDENCY` | Dev tools missing from the `dev` group | No. Run the printed `uv add --dev` command |
| `MISPLACED` | A dev tool sits in runtime `dependencies` | No. `uv remove` it, then add it to dev |
| `VERSION` | `uv.lock` holds a dev tool outside its `specifier` in `toolsets.toml` | No. Run the printed `uv add --dev` command; uv updates the constraint and re-locks |
| `BUILD` | Build backend is not `uv_build` | No. Migrate by hand (Adopt) |

Keys the baseline does not define are left alone. In ruff's rule lists (`select`, `extend-select`, `ignore`, `per-file-ignores`), only the baseline's own entries are checked: a missing one is `MISSING`, and a project's added rules stay. A project's added ignores stay too, reported as `RELAXED`. `[tool.vulture] ignore_names` and `[tool.coverage.run] source` are added if missing and never compared after that. What each tool's keys do is set in `assets/pyproject/toolsets.toml`.

In review mode, a `DIFFERS` line is a question, not an order. A project may have a reason for its value. Report it and let the user decide.

## Typing modes

basedpyright's `typeCheckingMode` is the scale. Its VS Code extension reads `[tool.basedpyright]`, so the editor and `uv run poe typecheck` agree. The script keeps the other tools in step:

| Mode | basedpyright | ruff annotation rules | ty | pyrefly `preset` |
| --- | --- | --- | --- | --- |
| `off` | off | none | defaults, warnings pass | `off` |
| `basic` | basic | public return types only | defaults, warnings pass | `basic` |
| `standard` | standard | `ANN`, `Any` allowed (`any-type` ignored) | defaults, warnings fail | `default` |
| `strict` | strict on `src/`, standard on tests | `ANN` including `any-type` | every rule an error | `strict` |

Ruff's preview mode wants single rules selected by name, not code (`too-many-branches`, not `PLR0912`); its `rule-codes-in-selectors` check flags codes. Category prefixes such as `ANN` or `E5` are fine. Follow this in any project config you write.

Strict mode is written as `typeCheckingMode = "standard"` plus `strict = ["src"]`, so tests stay at standard. Strict mode's extra rules fight test code (fixtures, fakes, deliberately loose inputs), and ruff already relaxes tests the same way through `per-file-ignores`. The script reads that pair as strict, and moves a plain `typeCheckingMode = "strict"` to it.

New projects start at `standard`. In `strict`, every exception is named: a rule severity in config or a coded `# pyright: ignore[rule]`, with a comment saying why.

basedpyright is the command-line checker and the pre-commit gate. It is a fork of pyright that ships as wheels, so uv.lock pins it and its Node.js runtime; the `pyright` PyPI package downloads both on first run instead. A project on pyright gets `CONFLICT tool.pyright`: move its settings to `[tool.basedpyright]`, swap the dev dependency, and replace Pylance with `detachhead.basedpyright` in `.vscode/extensions.json`.

ty and pyrefly are optional: configure them only when the user uses one. For ty, also add `astral-sh.ty` to `.vscode/extensions.json`.

## Linter failures are structural signals

Complexity, argument-count, file-length, and vulture failures mean the code needs restructuring. `CONTRIBUTING.md` says how to handle each one. Do not raise a threshold or add a `noqa` to get a check to pass. A threshold change is the user's call, recorded in `AGENTS.md` with the reason.
