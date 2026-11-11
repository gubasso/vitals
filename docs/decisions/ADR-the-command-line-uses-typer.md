# The command line uses Typer

## Context and Problem Statement

`vitals` takes six flags, validates them through the pydantic configuration, and maps every failure to a sysexits code in `main`. exobrain-tech names Typer for a Python command line, and the typing contract must hold on the code that declares the flags.

## Considered Options

- `Typer` — chosen.
- `cyclopts` — rejected: it is typed end to end too, but Typer passed the gate, and the canon already names it.
- `click` — rejected: its decorators carry the types apart from the function signature.

## Decision Outcome

Chosen option: `Typer` — Typer 0.29.1 declares each flag as an `Annotated` parameter, and mypy strict with `explicit-any` passes on the command with no ignore.

- The command runs with `standalone_mode=False`, so Typer returns the parsed request and never exits. `main` stays the one exit boundary.
- Typer 0.29 vendors click under a private module. The code catches the public `typer.TyperException`, which every usage error inherits, and imports nothing private.
- The flags only fill the first layer of the pydantic-settings model, which validates every value.

Enforced by `cli:the-flags-select-the-run` and `cli:main-is-the-one-exit-boundary`.

## Consequences

- Good: the help text lists every flag and the views of the registry.
- Bad: a Typer release that changes its vendored click can change the text of a usage error.

## Status

Accepted.
