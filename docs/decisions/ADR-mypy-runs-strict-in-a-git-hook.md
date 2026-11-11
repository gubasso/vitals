# mypy runs strict in a git hook, from the project venv

## Context and Problem Statement

The typing contract is worth only what a check enforces on every commit. The check must load the pydantic and returns plugins, and each plugin must match the library version the program runs, or it judges types the program does not have.

## Considered Options

- `mypy strict in a system hook that runs uv run mypy` — chosen.
- `mypy from pre-commit/mirrors-mypy with the typed libraries in additional_dependencies` — rejected: the plugins would load the versions of the hook configuration, a second pin beside `uv.lock` that drifts from it.
- `pyright` — rejected: it loads no plugin, so it cannot read the pydantic models or the `returns` containers as their plugins describe them.

## Decision Outcome

Chosen option: `mypy strict in a system hook that runs uv run mypy` — mypy 2.4.1 is current, and its `exhaustive-match` error code fails a `match` on a `Result` or an enum that misses a case. Source: [mypy optional error codes](https://mypy.readthedocs.io/en/stable/error_code_list2.html).

- mypy is a dev dependency in `pyproject.toml`, and `uv.lock` pins it with the plugins.
- The hook keeps `language: system`, class `project-environment`, with its owner comment. The reason is specific to this repository: the two plugins must load the versions of `uv.lock`.
- The configuration lives in `[tool.mypy]` of `pyproject.toml`, so the hook, the task runner, and an editor run one check.

Enforced by `typing:mypy-runs-strict-with-the-extra-codes`.

## Consequences

- Good: a commit that breaks the contract fails before it lands.
- Good: one lock owns mypy, the plugins, and the libraries they read.
- Bad: the hook needs the devshell and the venv, so it runs only through `direnv exec` or an activated shell.

## Status

Accepted.
