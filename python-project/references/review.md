# Review

Report how an existing uv-managed project drifts from the baseline.

Report only. Change nothing until the user approves.

1. Run `sync-pyproject` in report mode.
2. Compare each copied file with its source: `diff` the project's `.pre-commit-config.yaml`, `devbox.json`, `.vscode/*`, and `scripts/*.py` against the assets, and the body of `CONTRIBUTING.md` against `references/python.md` (frontmatter stripped as in step 3 of [init.md](init.md)). Check `.gitignore` for missing lines and `AGENTS.md` for the CONTRIBUTING pointer. Compare the `uv@` pin in `devbox.json` with `devbox search uv`, not with the asset's pin, and report a newer uv as drift. If devbox is not installed, skip that comparison and say so in the report; do not install devbox to run it.
3. Check the layout: `src/<package>/`, no `tests/__init__.py`, absolute imports, and `requires-python` at 3.12 or newer.
4. Read the code against `references/python.md`. Sample the largest and most recently changed modules rather than reading everything. Look for what tools cannot see: positional calls into the project's own functions, public functions without a bare `*`, `os.path`, missing pydantic at input boundaries, tests that could reach the network or real credentials.
5. Run the checks if the environment allows (`uv run poe check`) and record failure counts per tool. Before running any task in a project you did not set up, read its `[tool.poe]` tables, including any files `[tool.poe] include` names, and confirm each task runs what its name says. A task can run anything, so treat a project's tasks like its Makefile.
6. Write the report:

```markdown
## <project> - python-project review

**Typing mode:** <mode> | **Coverage:** <total>% (fail_under <n>) | **Lint:** <n> findings | **Typecheck:** <n> errors

### Config drift
<sync script findings, grouped; each DIFFERS line with a recommendation>

### Files
<missing or differing project files>

### Conventions
<code-level findings from step 4, each with file:line and the rule from CONTRIBUTING.md>

### Suggested order
<numbered changes, smallest blast radius first>
```
