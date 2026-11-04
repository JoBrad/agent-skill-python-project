# AGENTS.md

This file serves as instructions for agents.

Process the `README.md` file in the root of this repo. It contains an overview of what this project is for.

## Project goals

This project is for developing a skill for using in Python-based projects. It provides an opinionated structure that should be applicable to projects of any size, and is based on modern industry-accepted best practices and the Zen of Python. Think of it as Black, but for the entirety of a Python project.

The skill does not aim to, and cannot, provide an answer to every possible project requirement. But it should provide a SOLID (get it, hehe) baseline for mature Python development.

Installation of the skill directly from the repository should be supported, without requiring the user to build any of the supporting tools required by the script. Additionally, files that are only required for developing the skill and its supporting features should not be included as part of the skill, except as required to actually execute it. NOTE: Since the skill is for Python projects, it is assumed to be acceptable to require the user to install Python and a Python package manager.

The skill should also enable agent-based development, both alongside and independent of human-involved development.

Like all things Python, including a good sense of humor and self-deprecation is paramount to victory.

## Project organization

The skill is `python-project/`. Everything else in the repo is the development environment for it and never ships.

```txt
.
├── .vscode/
|   From the skill's own assets. Not part of the skill.
├── evals/
|   Evals for the skill: evals.json (skill-creator's format) and the fixture projects
|   in files/ that the prompts start from. Run output goes to python-project-workspace/,
|   which is gitignored. Not part of the skill.
├── python-project/
|   The skill. Everything here ships when the skill is installed.
|   ├── assets/
|   |   Files the skill copies into a project, including assets/scripts/*.
|   ├── references/
|   |   Docs the skill reads. python.md is copied into a project as CONTRIBUTING.md.
|   ├── src/python_project/
|   |   Code the skill runs in place (`sync-pyproject`). Never copied into a project.
|   ├── SKILL.md
|   └── pyproject.toml, uv.lock
|       The skill's runtime package. `uv run --project <SKILL_DIR>` builds
|       <SKILL_DIR>/.venv from these on first use.
├── schemas/
|   JSON Schemas for the skill's data files (toolsets.schema.json). Not part of the skill.
├── tests/
|   Tests for the skill's package and its asset scripts. Not part of the skill.
├── .gitignore
|   Super tailored to this project. It should stay that way.
├── .pre-commit-config.yaml
|   From the skill's own assets. Not part of the skill.
├── AGENTS.md
|   This file! It is primarily for agents, not humans.
├── CLAUDE.md
|   Just includes a reference to this file.
├── CONTRIBUTING.md
|   Copy of python-project/references/python.md, frontmatter stripped.
├── LICENSE
|   License detail for this project.
├── README.md
|   An overview file primarily for humans. Agents should also read it.
├── devbox.json, devbox.lock
|   Development environment for working on this repo. Not part of the skill.
└── pyproject.toml, uv.lock
    Development dependencies and tooling. Not part of the skill.
```

## Working on the skill

The skill is the content of `python-project/`: `SKILL.md`, `references/`, `assets/`, and the runtime package.

Code in the skill falls in two places. `python-project/src/python_project/` runs from the skill directory through its own venv. `python-project/assets/scripts/` holds standalone scripts that a project receives as copies and runs through that project's venv, so they may import only the standard library. Both are tested from `tests/`: the package imports as `python_project`, and `tests/conftest.py` puts the asset scripts on `sys.path` so they import by module name.

### Skill checks

When the skill is updated, you should perform several checks:

- Use Anthropic's `skill-creator` skill, invoked by its full name `anthropic-skills:skill-creator`, to review changes to this skill. Any new updates should be reviewed by this skill before publishing. `anthropic-skills:` is a namespace reserved for skills synced from claude.ai, so no local or third-party skill can take that name; do not substitute another skill-creating or skill-testing skill.
- Except for noted requirements, the skill should be self-contained, and not require any other skills or tools.
- Nothing in the skill should reference resources (e.g. color palettes, etc.) that are not part of the skill, or would violate either the license of the utilized resource or the licensing of this skill.
- Scan the skill detail to ensure secrets, keys, etc. are not included. Nothing in the skill should require access to privileged info. If present, you may use a tool such as `gitleaks` to scan the code.
- Use neutral names in every example and reference in the skill (`<package>`, `orders`, `fetch_orders`), not names from a real project. Skill resources never mention a specific user.
- All Python-based code in this project should adhere to the skill's instructions regarding a well-formed python project.

### Installing the skill

There are instructions on using the `gh` CLI to install the skill in the README.md file. An advanced user may also wish to simply use a symlink to install the skill, targeting a locally-cloned copy of the repository.

## Working on the Python code

Read [CONTRIBUTING.md](CONTRIBUTING.md) before writing code. It holds the Python conventions for this project. Project-specific exceptions to it are listed under Conventions below, and they win.

### Commands

Checks run as Poe the Poet tasks (`uv run poe <task>`), defined in `[tool.poe.tasks]` in `pyproject.toml`; `uv run poe` lists them. `devbox run <task>` runs the same task, and devbox adds `install` and `run`.

| Command | Description |
| --- | --- |
| `devbox run install` | `uv sync`, then install the pre-commit hooks |
| `uv sync` | Create or update `.venv` from `uv.lock` |
| `devbox run run` | Run the skill's `sync-pyproject` against this repo, report only |
| `uv run poe test` | Run the test suite |
| `uv run poe lint` | Lint with ruff |
| `uv run poe file-length` | Enforce the 500-line file limit |
| `uv run poe format` | Ruff format, then apply ruff's safe fixes |
| `uv run poe format-check` | Check formatting without changing files |
| `uv run poe typecheck` | basedpyright at the mode in `[tool.basedpyright]` |
| `uv run poe coverage` | Tests with coverage; fails under `fail_under` in `[tool.coverage.report]` |
| `uv run poe coverage-diff` | Coverage of lines changed since the merge base; fails under 90% |
| `uv run poe deadcode` | Vulture - report unused code |
| `uv run poe check` | lint, format-check, file-length, typecheck, coverage, and deadcode in turn |

Run a single test:

```bash
uv run pytest tests/test_sync_pyproject.py::test_name -v
```

After changing `python-project/pyproject.toml`, run `uv lock --project python-project` and `uv sync`. Pre-commit checks both lock files.

### Conventions

This repo is the skill's own source, so it departs from the baseline it ships:

- Typing mode: `standard` (`[tool.basedpyright] typeCheckingMode`).
- No root `src/`. The package lives in `python-project/src/`, so `[tool.basedpyright] include` and `[tool.vulture] paths` name the skill's paths. `sync-pyproject` reports both as `DIFFERS`; keep this repo's values.
- The root project is `package = false` with no build backend, so `sync-pyproject` reports `BUILD`. The skill package in `python-project/` uses `uv_build`.
- `evals/files/` holds fixture projects, some deliberately off the baseline. Root `[tool.ruff] extend-exclude` and a top-level `exclude` in `.pre-commit-config.yaml` keep them out of this repo's checks; the pre-commit one is needed because ruff lints an explicitly passed fixture file under the fixture's own `pyproject.toml`.
- `check_file_length.py` and `changed_lines_coverage.py` run in place from `python-project/assets/scripts/` rather than as copies in `scripts/`, so the repo tests the same files it ships. `sync-pyproject` reports the `file-length` and `coverage-diff` tasks as `DIFFERS`; keep this repo's paths.

## Requirements

1. `uv`: Used to install dependencies for several python scripts, and to invoke them.

You should prompt the user to install these requirements if they are missing. You should not attempt to install any applications unless explicitly directed to do so by the user.

### Check for `uv`

Run the following command to check if `uv` is installed:

```bash
uv --version
```

If `uv` is not installed, you have 2 options:

1. (Preferred): When working from this repo, use `devbox`. Prompt the user to install `devbox` if it is not installed. Then run `devbox run install` to setup the virtual environment. Devbox is for development only; the skill itself never uses it.
2. Prompt the user to install `uv` from its official source: `https://docs.astral.sh/uv/getting-started/installation/`
