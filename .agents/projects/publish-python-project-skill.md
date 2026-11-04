---
type: project
status: active
created: 2026-11-03
tags: [publishing, skill]
branch: feature/initial-deploy
---

# Publish the python-project skill on GitHub so anyone can install it with `gh skill install`

Joseph built the python-project skill up over time as a private, installed copy. This project turns it into a public repo, JoBrad/agent-skill-python-project, that is plainly a skill repo: the skill lives in `python-project/` and ships as-is with no build step, and everything else in the repo is dev tooling for it. Priority order: get the skill content right first, then make the installation instructions accurate. Done means the repo's checks pass (`devbox run check`), the skill-creator review is clean, and the README's install commands have been run against the published repo and install a working skill.

## Decisions

- [x] 2026-11-04 - Evals: a top-level `evals/` folder, tracked. `evals.json` holds the eval set in skill-creator's format, and `evals/files/` holds the fixture projects. Only run output (`python-project-workspace/`) is gitignored.
- [ ] Release strategy: `gh skill install` resolves the latest tag before the default branch, so decide whether to tag releases or let installs track `main`.
- [x] 2026-11-03 - `sync-pyproject` list keys (`select`, `extend-select`, `ignore`, `per-file-ignores.*`): drift is only the baseline's own entries. A baseline entry the project lacks is `MISSING` and gets added. An entry the typing mode forbids (`ANN` outside standard and strict, `any-type` outside standard) is `EXTRA` and gets removed. A project's extra `select` entries are left alone. A project's extra ignores turn checks off, so they are reported for review and left alone. Prefixes covering codes (`E` vs `E1`) are not resolved; a false `MISSING` is accepted.
- [ ] Revisit the skill venv decision? `uv run --project <SKILL_DIR>` writes `<SKILL_DIR>/.venv` and fails on a read-only install (plugin cache, shared install). A PEP 723 script run with `uv run --script` keeps its environment in uv's cache and drops the skill's own `pyproject.toml` and `uv.lock`. (added 2026-11-03)
- [x] 2026-11-04 - skill-creator test prompts live in the root `evals/evals.json`, not `python-project/evals/`, so they never ship.
- [x] 2026-11-03 - Task runner: Poe the Poet (`[tool.poe.tasks]`, run as `uv run poe <task>`). MIT, actively developed, configured in `pyproject.toml`, no extra binaries. devbox only exists in the target project, and it is optional there, so it cannot be the layer the skill runs. Surveyed: Make, shell scripts, just, nox, and tox; uv has no task runner (astral-sh/uv#5903).
- [x] 2026-11-03 - Type checker: basedpyright, not pyright. The `pyright` PyPI package downloads Node.js and pyright on first run, outside `uv.lock`. basedpyright ships both as wheels, so the lock pins them. Same modes and `strict` paths; config in `[tool.basedpyright]`; VS Code extension `detachhead.basedpyright` replaces Pylance. A project's `[tool.pyright]` is reported `OBSOLETE`.
- [x] 2026-11-03 - `sync_pyproject.py` line limit: split into `models`, `toolsets`, `dependencies`, and `sync_pyproject` along the manifest seam. No exception.
- [x] 2026-11-03 - devbox scripts: each wraps `uv run poe <task>`. devbox stays optional and supplies uv.
- [x] 2026-11-03 - Tool choice per function: `[tool_selections]` in `toolsets.toml` names the package for each function, and `[task_requirements]` names the Poe tasks each function must provide. Each package supplies its own tasks; packages live under `[packages.*]`.
- [x] 2026-11-03 - Repo layout: two `pyproject.toml` files. `python-project/` holds the skill's runtime package and its own `uv.lock`, and the root is a dev-only environment (`package = false`), matching agent-skill-iso-diagram.
- [x] 2026-11-03 - Build step: none. `sync-pyproject` runs from source through `uv run --project <SKILL_DIR>`, and asset scripts ship in final form, so the published location is the installed location.
- [x] 2026-11-03 - Skill venv: lives in `<SKILL_DIR>/.venv`, separate from the user's project. A `--from-local` install copying the repo's `.venv` is accepted; uv rebuilds it on first run, and most installs come from GitHub.
- [x] 2026-11-03 - `install_uv.sh`: removed. devbox's uv package carries the GHSA-hq85-5cpj-mr62 fix.
- [x] 2026-11-03 - Version numbers: kept out of steering docs and READMEs. They live in `pyproject.toml`, lock files, and `devbox.json`.
- [x] 2026-11-03 - Older projects: no migration or cleanup support. This is a first public release.
- [x] 2026-11-04 - Python floor: 3.12, for the `type` statement in `python.md`. Init requires it. Adopt and Review report a lower `requires-python` and raise it only with approval.
- [x] 2026-11-03 - AGENTS.md shape: goals, organization, working on the skill, working on the Python code, requirements.

## Tasks

### Skill content

- [x] Init the repo as a uv project and move `sync_pyproject.py` into the skill package (done 2026-11-03)
- [x] Reorder README sections (done 2026-11-03)
- [x] Restructure AGENTS.md into skill and Python sections (done 2026-11-03)
- [x] Split SKILL.md by scenario into `references/init.md`, `adopt.md`, `review.md`, and `typing-mode.md`, replacing the `project-init.md` draft (added 2026-11-03, done 2026-11-03)
- [x] Fix "Changing a project's mode" steps 2 and 5: pyright, ruff, and pre-commit run in the target project's venv, not `--project <SKILL_DIR>` (done 2026-11-03)
- [ ] Settle the SKILL.md working-files instruction: one term for the files, decide on "memory files", and add any line it needs to the gitignore template. Review note: as written (SKILL.md line 47), nothing in the workflow creates working files, so the line mostly prompts a needless question, and its style differs from the rest of the file. Either tie it to a concrete file or cut it. No longer tied to evals, which moved to the root `evals/` (2026-11-04). Joseph (2026-11-04): keep the line; files an agent creates while rewriting code also belong there.
- [x] Move the tool list into `assets/pyproject/toolsets.toml` (packages keyed by name, with `functions`, `default_for`, `config_file`, `dev_dependency`, `display_name`) and drop the version floors from `sync-pyproject` (added 2026-11-03, done 2026-11-03)
- [x] Move per-tool knowledge out of `sync_pyproject.py` into `toolsets.toml`: `add_if_missing`, `remove_if_present`, `conflicting_settings` (new `CONFLICT` finding), `adds_to`, `relaxes`, `build_backend`, and `typing_modes`, with forbidden keys and entries derived from the modes (added 2026-11-03, done 2026-11-03)
- [x] Add `CONFLICT` to the SKILL.md report table, and say what Review and Adopt do with one (added 2026-11-03, done 2026-11-03)
- [x] Split `sync_pyproject.py` into `models`, `toolsets`, `dependencies`, and `sync_pyproject`; add a `specifier` per package in `toolsets.toml` and a `VERSION` finding checked against the project's `uv.lock`, using `packaging` (added 2026-11-03, done 2026-11-03)
- [x] Add Poe the Poet tasks to the baseline, switch the skill's docs and this repo to `uv run poe <task>`, and check the task contract in tests (added 2026-11-03, done 2026-11-03)
- [x] Write a JSON Schema for `toolsets.toml`, point the file at it with a `#:schema` line so Even Better TOML validates and completes it, and validate the manifest against it in a test. Use the field descriptions from the header removed after fe91378 as the schema's `description` text. (added 2026-11-03, done 2026-11-03)
- [ ] 🌱 Backlog: Alternative toolsets (e.g. black for format). Needs a per-function "choose one or add alongside" rule, typing-mode overlays per linter, tools not configured in pyproject (flake8), and SKILL.md steps for hooks, devbox, and VS Code. Belongs in its own project after the publish. (added 2026-11-03)
- [x] 🪦 Dropped: `min_version` - replaced by the full `specifier` field (done 2026-11-03)
- [ ] 🌱 Backlog: Integrate `update_pyproject_dependencies.py` into the skill package
- [ ] 🌱 Backlog: Skill checks tooling (`scripts/check_skill.py` for frontmatter, referenced paths, private paths, and versions in prose; gitleaks on `python-project/`)
- [x] Review the skill with skill-creator (done 2026-11-03). Findings are the tasks below and the review notes under Notes.

#### Review findings (added 2026-11-03)

- [x] Make `sync-pyproject --write` behavior on list keys match the list-keys decision, with a test per case (done 2026-11-03)
- [x] Add `.devbox/` to `assets/.gitignore-template` (done 2026-11-04)
- [x] Fix Adopt step 4: name which Init steps apply. Init step 4 (reshape the `main()` that `uv init` generates) may not fit a project with real code. Adopt step 2 (`uv init --package` in place) and step 3 (move code under `src/`) can collide over `src/<package>/__init__.py`. Moved the code move ahead of `uv init`, which leaves an existing `__init__.py` alone but still writes a `[project.scripts]` entry for a missing `main()`; Adopt now repoints or deletes it and skips Init step 4. (done 2026-11-04)
- [x] Replace origin-project examples in `references/python.md` (`resolve_vertical`, `VerticalName`, `get-transcripts`, `session.client("sts")`) with neutral names (done 2026-11-03)
- [x] Write skill-creator test prompts: init in an empty dir, adopt a `requirements.txt` project, review a drifted project, change typing mode. Four evals in `evals/evals.json` with fixtures in `evals/files/` (done 2026-11-04)
- [ ] Run the evals with skill-creator, with and without the skill, and turn failures into tasks (added 2026-11-04)
- [ ] 🧩 Refining: Explain or remove the `paths:` frontmatter in `references/python.md`. If it exists so the file can go in `.claude/rules/`, say so in SKILL.md; otherwise drop it and the awk strip step. Joseph links `~/.claude/rules/python.md` to the installed `references/python.md`, so the frontmatter scopes the rule there (2026-11-04).
- [x] Reconcile the Python floor: `python.md` recommends `type X = ...` (3.12+), while Init step 1 lets the user pick any floor Floor is 3.12: Init requires it, Adopt and Review report a lower `requires-python`. (done 2026-11-04)
- [x] Soften the positional-call rule in `python.md`: one parametrized `TypeError` test per module instead of one test per function (done 2026-11-04)
- [x] Say what Review does with the uv pin when devbox is not installed. Skips the comparison and says so; never installs devbox. (done 2026-11-04)
- [x] Shorten the "Linter failures are structural signals" section in SKILL.md to a pointer to CONTRIBUTING.md, since `python.md` repeats it (done 2026-11-04)

### Installation instructions

- [x] Fix the README install commands: `OWNER/REPO` form, the `python-project` skill name, `--agent claude-code`, and `--from-local` taking the repo directory (done 2026-11-03)
- [ ] 🚧 Blocked: Run each README install command against the published repo - waiting on the first push to GitHub

### Publish

- [ ] Review every tracked file for sensitive or identifying info: secrets, private paths, names of people, employers, clients, or other projects. Run gitleaks over the repo and read the files gitleaks cannot judge. (added 2026-11-03)
- [ ] Open a PR from `feature/initial-deploy` to `main` once the major issues are resolved
- [ ] Reinstall `~/.claude/skills/python-project` from the repo, replacing the old layout

## Notes

- `gh skill install . --from-local` discovers the skill as `[root] python-project`. `gh skill install . python-project --from-local --dir <dir>` installs it, and the installed copy runs its own code after uv rebuilds the copied venv (checked 2026-11-03).
- Non-interactive `gh skill install` without a skill name only lists skills, and it defaults to the `github-copilot` agent.
- skill-creator review (2026-11-03): structure is sound. SKILL.md is 144 lines with one short reference per mode. `sync-pyproject` passes its 34 tests and runs clean against a fresh `uv init --package` project. The trigger description is specific and names the migration sources. AGENTS.md skill checks: self-contained, no external resources, no secrets found by reading every file (gitleaks not run).
- Reproduced the list-key overwrite (2026-11-03): with `extend-select = ["ANN", "S"]` and `S101` added to `per-file-ignores."tests/**"`, check mode reports both as `DIFFERS`. `--write` resets them to the baseline lists.
