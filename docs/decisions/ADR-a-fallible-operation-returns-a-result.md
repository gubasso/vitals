# A fallible operation returns a Result from returns

## Context and Problem Statement

A dashboard must keep drawing when one source fails: a missing GPU driver, a sensor the user cannot read, a mount that vanished. An exception can escape any call, and mypy cannot prove that a caller handles it. The operator asked for types as close to Rust as Python allows, where a failure is a value.

## Considered Options

- `Result from returns (dry-python)` — chosen.
- `rustedpy/result` — rejected: it has the Rust names, but its repository was archived on 2026-06-25.
- `Exceptions with an AppError hierarchy` — rejected inside the program: mypy cannot prove that a caller handles a raised error.

## Decision Outcome

Chosen option: `Result from returns (dry-python)` — returns 0.30.0 shipped on 2026-10-27, supports `match` on `Success` and `Failure`, and carries a mypy plugin. Sources: [returns](https://github.com/dry-python/returns), [Result docs](https://returns.readthedocs.io/en/latest/pages/result.html), [rustedpy/result](https://github.com/rustedpy/result).

- A fallible function returns `Result[T, E]`, and `E` is a typed error of its domain.
- `@safe` wraps a call into an untyped library in an adapter module, and nowhere else.
- `main` is the one boundary. It matches the `Result` of the run and maps a `Failure` to its sysexits code.

This amends the error-handling pattern of exobrain-tech, `languages/python/cli-spec/error-handling-python.md`, for this project. There, an `AppError` hierarchy raises up to `main`. Here, the `Result` travels up to `main`, and `main` maps it to the exit code as that chapter maps an `AppError`.

Enforced by `typing:a-fallible-operation-returns-a-result`, `typing:a-match-lists-every-case`, and `cli:main-is-the-one-exit-boundary`.

## Consequences

- Good: mypy proves that every caller handles both cases, through `exhaustive-match`.
- Good: a panel draws a `Failure` like any other value.
- Bad: a contributor learns the `returns` containers, and a stack trace shows less of the failure path.

## Status

Accepted.
