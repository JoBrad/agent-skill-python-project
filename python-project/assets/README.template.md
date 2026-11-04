# <project-name>

<!-- One paragraph: what this project does and why it exists. -->

## Prerequisites

- [uv](https://docs.astral.sh/uv/), at the version `[tool.uv] required-version` names - installs Python and the project's dependencies
- [devbox](https://www.jetify.com/devbox) (optional) - supplies uv, and runs each task as `devbox run <task>`

<!-- List every environment variable the program reads, what it is, and where to
     get it. Delete this section's comment when there are none. -->

## Quickstart

```bash
uv sync
uv run pre-commit install
uv run <script-name>
```

## Development

| Command | Description |
| --- | --- |
| `uv run poe test` | Run the test suite |
| `uv run poe lint` | Lint |
| `uv run poe format` | Format and apply safe fixes |
| `uv run poe typecheck` | Type-check with basedpyright |
| `uv run poe coverage` | Run tests with coverage |
| `uv run poe check` | Every check, including formatting, the file-length limit, and a dead-code report |

`uv run poe` lists every task. Conventions for contributors are in [CONTRIBUTING.md](CONTRIBUTING.md).
