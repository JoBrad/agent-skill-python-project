# Init

Scaffold a new project on the baseline.

Starting point: an empty directory, or one with no `pyproject.toml`. It may already be a git repository.

1. Confirm the package name and the Python floor, which is 3.12 or newer: `CONTRIBUTING.md` uses the `type` statement. `uv init` picks the newest installed Python unless told otherwise. If a parent directory has a `pyproject.toml`, `uv init` adds the new project to it as a workspace member and rewrites its `uv.lock`: ask whether the new project should join that workspace, and if not, pass `--no-workspace`.
   ```bash
   uv init --package --name <name> [--python 3.14] [--no-workspace] .
   ```
2. Run `sync-pyproject` in report mode. Run the `uv add --dev` command it prints (add `--with ty` or `--with pyrefly` to the script first if wanted). Then apply the tables:
   ```bash
   uv run --project <SKILL_DIR> sync-pyproject --project . --write
   ```
3. Copy and fill in the files from the baseline table in `SKILL.md`. For `CONTRIBUTING.md`, ask the user once, in one message, for the repo conventions its template asks about: where issues go, a code of conduct, the default branch and whether direct commits are allowed, branch naming, commit message format, pull requests and review, and the secret scanner. Fill in the template from the answers, and delete any section the user gave nothing for rather than inventing policy. Then append the Python conventions without their frontmatter:
   ```bash
   awk 'NR==1 && /^---$/ {fm=1; next} fm && /^---$/ {fm=0; next} !fm' \
     <SKILL_DIR>/references/python.md >> CONTRIBUTING.md
   ```
   When the project already has a `CONTRIBUTING.md`, keep its content, and add the `## Python conventions` section or replace an existing one.
   Set the `run` script in `devbox.json` and the `<script-name>` in README and `AGENTS.md` to the command in `[project.scripts]`.
4. Reshape what `uv init` generated, which fails the baseline's lint: it puts `main()` in `src/<package>/__init__.py` with no docstrings. Move `main` to `src/<package>/cli.py` with a module and function docstring, leave `__init__.py` holding only a docstring, and point `[project.scripts]` at `<package>.cli:main`. Then write `tests/test_cli.py` for it, so coverage starts above its threshold.
5. `uv run pre-commit install`. If the directory is not a git repository, say the hooks are inactive until it is.
6. Verify, and fix anything that fails: `uv run poe check`, which runs every check in turn.
7. Report what was created.
