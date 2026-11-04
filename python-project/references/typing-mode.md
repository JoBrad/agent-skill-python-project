# Changing a project's typing mode

A mode set only in `pyproject.toml` is a wish. It holds once something enforces it on every commit, so a mode change covers the enforcement too. The modes and what each one sets are in the typing-mode table in `SKILL.md`.

basedpyright, ruff, and pre-commit below run in the project's own environment, so call them with plain `uv run`. Only `sync-pyproject` runs through `--project <SKILL_DIR>`.

1. Run `sync-pyproject` with `--typing-mode <mode> --write`.
2. Check `.pre-commit-config.yaml` against `assets/pre-commit-config.yaml`. The `typecheck` hook (`uv run basedpyright`) is what holds the mode on each commit, and the ruff hook carries the annotation rules. Add or update the hooks when they are missing or differ; create the file from the asset when there is none. The mode change is the reason, so this needs no separate approval.
3. Check that `[tool.poe.tasks]` has the `typecheck` task, and update the typing mode line under Conventions in `AGENTS.md`.
4. If the project is a git repository, run `uv run pre-commit install`. If it is not, say the hooks are inactive until it is.
5. Run `uv run poe lint` and `uv run poe typecheck` and report what the new mode costs: counts per tool and per kind of finding, the root causes, and a suggested order. Do not fix the code unasked.

Report the files you changed for enforcement alongside the cost, so the user sees both what was switched on and what now stands between them and a passing commit.
