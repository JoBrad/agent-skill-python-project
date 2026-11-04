# Code review

Review a project's code against the conventions in `references/python.md`, the file a project receives as `CONTRIBUTING.md`. A project review ([review-project.md](review-project.md)) centers on config and files; a code review centers on the code.

Report only. Change nothing until the user approves.

1. Set the scope: the modules, paths, or changes the user named, or the whole package and its tests when they named none. Say which in the report.
2. Run the checks as in step 5 of [review-project.md](review-project.md), including its rules for reading the project's tasks first and using a scratch copy. The tool findings fill the Check results table; do not repeat them one by one as findings.
3. Read every module in scope against `references/python.md`, not a sample. Look first for what the tools cannot see:
   - positional calls into the project's own functions, in source and tests
   - public functions without a bare `*`
   - `os.path` or bare `open()` where the convention is `pathlib`
   - data parsed from outside the program with no pydantic model at the boundary
   - a value that fails to resolve and is silently dropped
   - tests that could reach the network, real credentials, or an interactive login
   - functions doing too much, where a linter limit was raised or ignored instead of the code restructured
4. Write the report:

```markdown
# python-project code review: <project name>

## Check configuration

<typing mode, type checkers, coverage fail_under, and the scope of this review>

## Check results

| Check | Result |
| --- | --- |
| Lint | <n> findings |
| Format | <clean or n files> |
| Typecheck | <n> errors |
| Coverage | <total>% (fail_under <n>) |
| Dead code | <n> findings |
| File length | <pass or files over the limit> |

Config and file drift are not covered here; a project review reports them.

## Findings

### <path>

- <file:line> - <what the code does> - <the CONTRIBUTING.md rule it breaks>

## Suggested order

<numbered changes, smallest blast radius first>
```
