# orders

Read [CONTRIBUTING.md](CONTRIBUTING.md) before writing code. It holds the Python conventions for this project. Project-specific exceptions to it are listed under Conventions below, and they win.

## Commands

Tasks run through Poe the Poet (`uv run poe <task>`), defined in `[tool.poe.tasks]` in `pyproject.toml`; `uv run poe` lists them. With devbox, `devbox run <task>` runs the same task.

| Command | Description |
| --- | --- |
| `uv sync` | Create or update `.venv` from `uv.lock` |
| `uv run orders` | Run the program |
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

`orders` reads a JSON list of orders and prints each order's total in cents.

- `src/orders/cli.py`: the entry point. Parses arguments and prints.
- `src/orders/pricing.py`: loads orders and computes totals.

## Conventions

- Typing mode: `standard` (`[tool.basedpyright] typeCheckingMode`).
