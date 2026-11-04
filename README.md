# Python-project skill

## Overview

This skill provides an opinionated way of creating and working in a well-formed Python project.

## What it does

- **Init**: Sets up a new project.
- **Adopt**: Moves an existing pip, poetry, hatch, or setuptools project onto `uv` and the baseline.
- **Review**: Reports how an existing project differs from the baseline. Nothing is changed without your approval.

## What is a well-formed Python project?

- Code is committed to a repository
- Adheres to the PyPA `pyproject.toml` specification for project configuration, tooling, and build configuration. This project uses `uv`.
- Code lives in `src/<package>/` and uses absolute imports only.
- Tests are defined in a top-level `tests/` folder. Test coverage for new code is [at or above 90%](./python-project/assets/pyproject/tool.coverage.toml).
- A linter such as `ruff` is used to apply linting and formatting rules. This skill includes a [configuration preset](./python-project/assets/pyproject/tool.ruff.toml) for `ruff`. Hitting a complexity or file-length limit means the code needs restructuring, not a higher limit.
- Type checking is enforced. This skill defines [4 levels of type checking](./python-project/references/python.md) based on `basedpyright`.
- Dead code is removed. This skill uses `vulture` for this.
- Checks run on every commit. This skill uses `pre-commit`.
- People and agents follow the same [Python conventions](./python-project/references/python.md).

## Selected tooling

The skill defines several [project-level functions](./python-project/assets/pyproject/toolsets.toml) with associated tooling to fulfill each:

- `package-manager`: [uv](https://docs.astral.sh/uv/): Manages Python, the virtual environment, and dependencies, with a lock file. Fast, and replaces pip, venv, and pip-tools.
- `lint`: [Ruff](https://docs.astral.sh/ruff/): Linter and formatter. One fast tool replaces flake8 and its plugins, isort, and black.
- `format`: Also uses `ruff`
- `test`: [pytest](https://docs.pytest.org/) and [coverage.py](https://coverage.readthedocs.io/) (through [pytest-cov](https://pytest-cov.readthedocs.io/)): Tests and coverage. The standard choices.
- `coverage`: [pytest-cov](https://github.com/pytest-dev/pytest-cov): coverage plugin for pytest.
- `typecheck`: [basedpyright](https://docs.basedpyright.com/): Type checker. A fork of Microsoft's [Pyright](https://github.com/microsoft/pyright) that ships as Python wheels, so `uv.lock` pins it and the Node.js runtime it needs. The `pyright` package downloads both on first run instead. Its VS Code extension uses the same config, so the editor and the command line agree. [ty](https://github.com/astral-sh/ty) and [Pyrefly](https://pyrefly.org/) are supported as optional extras.
- `deadcode`: [Vulture](https://github.com/jendrikseipp/vulture): Finds dead code.
- `tasks`: [Poe the Poet](https://poethepoet.natn.io/): Task runner. Every check runs as `uv run poe <task>`. It's MIT-licensed, in active development, and has a robust feature set. It lets the skill support a variety of tooling, all managed in `pyproject.toml`, without requiring additional binaries.
- `hooks`: [pre-commit](https://pre-commit.com/): Runs the checks on every commit.

The skill sets tool in `pyproject.toml`, including runners (using Poe the Poet) with function-based names for ease of use.

```sh
# Run tests
uv run poe test

# Check test coverage
uv run poe coverage

# Format files
uv run poe format
```

## Requirements

To install and use the skill, the following applications are needed:

- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installs the skill's Python dependencies and runs its scripts.
- [`git CLI`](https://cli.github.com/) to install the skill.

For development, a [devbox](https://www.jetify.com/devbox) configuration is also provided.

## Installation

Use the [GitHub CLI](https://cli.github.com/manual/gh_skill_install) to install the skill. Note that you must have permission to write to the installation target.

The `--scope user` flag installs the skill in your home directory. Remove it to install the skill in the current git repository.

**From GitHub**

```sh
gh skill install JoBrad/agent-skill-python-project python-project --scope user
```

Use the [--agent](https://cli.github.com/manual/gh_skill_install) flag to pick the agent. Without it, `gh` asks, or defaults to GitHub Copilot in a non-interactive shell.

```sh
gh skill install JoBrad/agent-skill-python-project python-project --agent claude-code --scope user
```

**From a local clone**

```sh
gh skill install path/to/agent-skill-python-project python-project --from-local --scope user
```

Or symlink the skill folder from the clone's root:

```sh
ln -s "$PWD/python-project" ~/.claude/skills/python-project
```

## Development

The skill is the `python-project/` folder. Everything else is for developing it, and is not installed.

### Setup and commands

```bash
devbox run install    # or: uv sync && uv run pre-commit install
```

| Command | Description |
| --- | --- |
| `uv run poe test` | Run the test suite |
| `uv run poe lint` | Lint |
| `uv run poe format` | Format and apply safe fixes |
| `uv run poe typecheck` | Type-check with basedpyright |
| `uv run poe coverage` | Run tests with coverage |
| `uv run poe check` | Every check, including formatting, the file-length limit, and a dead-code report |

`uv run poe` lists every task. Conventions for contributors are in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

License detail is in [LICENSE](./LICENSE).

In short: Feel free to copy it, but keep it open, and please contribute your changes here. :)
