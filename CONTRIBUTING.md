
# Python conventions

How Python code is written in this project. People and coding agents follow the same rules. This file is copied from a shared baseline, so keep it identical to that baseline: record a project-specific exception in `AGENTS.md` instead of editing it here.

## Precedence

When two sources of guidance collide, the later one in this list wins.

1. **Industry practice.** SOLID, DRY, YAGNI. Fix what was asked and note the rest rather than chasing it. One concern per change, no drive-by refactors of code the change does not otherwise touch.
2. **The language's own conventions.** PEP 8, Python idioms, the standard library over a hand-rolled equivalent.
3. **This file.**
4. **Conventions observed in the codebase.** When the code does something consistently and nobody wrote it down, match the code.
5. **Explicit rules in `AGENTS.md`.** These override everything above. An anti-pattern or security flaw gets flagged for review, not followed or quietly worked around. Where the code consistently contradicts a written rule, raise it: one of the two is stale.

Tool config sits outside the ladder. The `[tool.*]` tables in `pyproject.toml` are enforced by pre-commit, so they win in practice. Read them before writing, and do not hand-write something the formatter will rewrite on the next commit.

## Environment

- The project is managed with `uv`. Run code with `uv run`, add dependencies with `uv add` (`uv add --dev` for tooling). Never `pip install`, never bare `python`.
- Tasks live in `[tool.poe.tasks]` and run as `uv run poe <task>`: `test`, `lint`, `format`, `typecheck`, `coverage`, `coverage-diff`, `deadcode`, `check`. `uv run poe` lists them. With devbox, `devbox run <task>` does the same.
- Ruff's config is the style authority for line length, quotes, import order, and indentation. Do not restate it and do not argue with it in review.
- Write LF line endings. Never commit a diff whose only content is a line-ending change.

## Structure

- Source lives in `src/<package>/`; tests live in `tests/`.
- Absolute imports only: `from <package>.<subpackage> import resource`. Relative imports are banned in config, which is also why module filenames are snake_case.
- CLI entry points register in `[project.scripts]` as a kebab-case command pointing at a snake_case module: `my-script = "<package>.<module>:function"`.
- Tests mirror the source tree: `src/<package>/orders/pricing.py` -> `tests/orders/test_pricing.py`. Shared fixtures go in `tests/conftest.py`, test-data builders in `tests/factories.py`. No `__init__.py` files under `tests/`; pytest's config handles imports.

## Calling functions

Pass arguments by name when calling a function defined in this project: `fetch_orders(customer_id=..., limit=...)`, not `fetch_orders(CUSTOMER_ID, 50)`. This applies in source and in tests. Named calls survive a reordered signature, and tests fail loudly on an API change instead of passing values into the wrong slots.

- Enforce it on public functions with a bare `*` at the start of the parameter list. Apply this to new or changed functions; do not retrofit untouched ones.
- Each test module holds one parametrized test that a positional call raises `TypeError`, with one case per keyword-only public function. A new function adds a case, not a test.
- Exceptions: positional-only parameters (builtins like `len`), exception messages, `*args` varargs, and calls into third-party libraries, which keep their usual form (`httpx.get(url)`, `subprocess.run([...])`).

## Tests

- Add tests for what you add or materially change, in the same change. Do not backfill coverage for untouched code unless asked.
- New code is at least 90% covered, branches included. `uv run poe coverage-diff` measures the lines changed since the merge base; report the number when handing work back.
- Tests never touch live credentials, the network, or an interactive login. Fake `subprocess.run`, sessions, and clients; isolate config through environment variables set in fixtures.

## Typing

The typing mode is `typeCheckingMode` in `[tool.basedpyright]`: `off`, `basic`, `standard`, or `strict`. basedpyright's editor extension reads it, `uv run poe typecheck` enforces it, and ruff's annotation rules follow it:

| Mode | Annotations ruff requires | `Any` |
| --- | --- | --- |
| `off` | None | Allowed |
| `basic` | Return types of public functions | Allowed |
| `standard` | Every parameter and return type | Allowed |
| `strict` | Every parameter and return type | Not allowed; each exception named in config |

In `strict`, basedpyright applies its strict rules to `src/` only (`strict = ["src"]`); tests are checked at `standard`, the same way ruff relaxes its rules for tests.

Change the mode in one place and re-run the baseline sync so ruff follows.

## Linter failures are structural signals

Treat these as a prompt to restructure, not to raise the threshold or add a `noqa`:

- `complex-structure` (complexity over 10), `too-many-branches`, `too-many-statements`: the function is doing too much. Decompose it.
- `too-many-arguments`, `too-many-positional-arguments`: group related parameters into a dataclass or pydantic model, or make them keyword-only.
- `scripts/check_file_length.py` (over 500 lines), or a module holding more than about two concerns: split it into a subpackage. No one is getting paid by lines of code.
- `vulture` (`uv run poe deadcode`): delete what it flags unless it is deliberately public API. Entry points go in `[tool.vulture] ignore_names`.

## Patterns worth matching

- **pydantic for anything parsed from outside the program.** Use `ConfigDict(extra="forbid")` for internal schemas where an unexpected key is a bug, and `extra="allow"` for human-edited data, where someone may have added a key the schema has not caught up to.
- **One accessor module per reference data file.** Exactly one module loads and validates a data file; nothing else carries a second copy of the table. Callers import the accessor.
- **Never duplicate a value list between a type and a data file.** Declare the type (`type Currency = Literal[...]`), derive the runtime tuple from it, and write a test that fails when the two drift.
- `functools.cache` on file-backed loaders.
- `pathlib` throughout, never `os.path`. Anchor with `ROOT_DIR = Path(__file__).resolve().parents[N]`.
- Module docstrings say why the module exists and what invariant it holds. Function docstrings say what a caller needs. Neither narrates the code.
- A value that fails to resolve surfaces for triage. Do not silently drop it.

## Design

- Defer abstraction until there is real duplication. Extract at the third copy, not the second. Read DRY as "do not repeat knowledge", not "never type a similar line twice".
- Separate explicit per-case code beats a shared generic layer written on speculation.
- Comments explain why, not what.
