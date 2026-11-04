# Skill evals

Tests for the skill itself: prompts a user might give, run by an agent with and without the skill, then graded against expectations. The unit tests in `tests/` check the skill's code; these check what an agent does when it follows `SKILL.md`. Nothing here ships with the skill.

## Layout

- `evals.json`: the eval set, in the format the Anthropic `skill-creator` skill reads. Each eval has a `prompt`, an `expected_output`, the `files` it starts from, and `expectations` a grader checks.
- `files/`: starting projects. Each run copies one into a scratch directory, so an eval never changes the fixture.
    - `adopt-requirements/`: pip and requirements files, with a flat package and relative imports.
    - `review-drifted/`: a uv project off the baseline in known ways: a `[tool.pyright]` table, an obsolete `target-version`, a looser `max-complexity`, an added ignore, missing dev tools, and code with positional calls and `os.path`.
    - `typing-mode-standard/`: a project on the baseline at `standard`, with code that fails `strict` in both basedpyright and ruff.

The init eval starts from an empty directory, so it has no fixture.

Fixtures carry no `uv.lock` or `.venv`. A run creates them with `uv sync`. The ruff config at the repo root excludes `files/`, because the fixtures are other projects and some are off the baseline on purpose.

## Running

Ask an agent to run the evals with `anthropic-skills:skill-creator` (Anthropic's skill-creator, by its full name), pointing it at `python-project/` as the skill and at this folder as the eval set. skill-creator expects `evals/evals.json` inside the skill directory; tell it the evals live at the repo root instead, and that `files` paths are relative to the repo root.

Run output goes to `python-project-workspace/` at the repo root, which is gitignored.

## Changing a fixture

A fixture's findings are part of its eval's expectations. After changing one, check it still produces them:

```bash
uv run --project python-project sync-pyproject --project evals/files/<fixture>
```

Then update the expectations in `evals.json` to match.
