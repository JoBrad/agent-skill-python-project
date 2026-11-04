# <project-name>

Read [CONTRIBUTING.md](CONTRIBUTING.md) before writing code or making a change. It holds this project's repo conventions (issues, branches, commits, pull requests) and its Python conventions. Project-specific exceptions to it are listed under Conventions below, and they win.

## Commands

Tasks run through Poe the Poet (`uv run poe <task>`), defined in `[tool.poe.tasks]` in `pyproject.toml`; `uv run poe` lists them. With devbox, `devbox run <task>` runs the same task.

| Command | Description |
| --- | --- |
| `uv sync` | Create or update `.venv` from `uv.lock` |
| `uv run <script-name>` | Run the program |
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
uv run pytest tests/<path>/test_<module>.py::test_name -v
```

## Architecture

<!-- What the program does, how data flows, and what each top-level module under
     src/<package>/ is responsible for. -->

## Conventions

<!-- Project-specific exceptions to CONTRIBUTING.md, each with the reason. Delete
     this comment when there are none. -->

- Typing mode: `<mode>` (`[tool.basedpyright] typeCheckingMode`).
