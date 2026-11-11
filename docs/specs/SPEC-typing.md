# Typing Specification

<!--TOC-->

- [Purpose](#purpose)
- [Requirements](#requirements)
  - [`typing:mypy-runs-strict-with-the-extra-codes` — mypy runs strict with the extra error codes](#typingmypy-runs-strict-with-the-extra-codes--mypy-runs-strict-with-the-extra-error-codes)
  - [`typing:a-fallible-operation-returns-a-result` — A fallible operation returns a Result](#typinga-fallible-operation-returns-a-result--a-fallible-operation-returns-a-result)
  - [`typing:a-match-lists-every-case` — A match lists every case](#typinga-match-lists-every-case--a-match-lists-every-case)
  - [`typing:pydantic-owns-every-boundary` — pydantic owns every boundary](#typingpydantic-owns-every-boundary--pydantic-owns-every-boundary)
  - [`typing:a-frozen-dataclass-owns-every-internal-value` — A frozen dataclass owns every internal value](#typinga-frozen-dataclass-owns-every-internal-value--a-frozen-dataclass-owns-every-internal-value)
  - [`typing:a-unit-is-a-newtype` — A unit is a NewType, and a closed set is a StrEnum](#typinga-unit-is-a-newtype--a-unit-is-a-newtype-and-a-closed-set-is-a-strenum)
  - [`typing:an-untyped-library-enters-through-one-adapter` — An untyped library enters through one adapter](#typingan-untyped-library-enters-through-one-adapter--an-untyped-library-enters-through-one-adapter)
  - [`typing:ruff-selects-every-rule-family` — ruff selects every rule family](#typingruff-selects-every-rule-family--ruff-selects-every-rule-family)
- [Unenforced](#unenforced)

<!--TOC-->

## Purpose

This domain covers the typing contract that every module of `vitals` meets: the strict type check, the `Result` rule for fallible operations, the types that carry data across a boundary and inside the program, and the lint rule set. It binds the code under `src/` and `tests/`. The behavior of the collectors, the dashboard, and the command line belongs to their own specs.

## Requirements

### `typing:mypy-runs-strict-with-the-extra-codes` — mypy runs strict with the extra error codes

The type check MUST run mypy with `strict`, `warn_unreachable`, the error codes `exhaustive-match`, `explicit-override`, `possibly-undefined`, `redundant-expr`, `truthy-bool`, `truthy-iterable`, `ignore-without-code`, `unused-awaitable`, `deprecated`, `mutable-override`, `redundant-self`, `unimported-reveal`, and `explicit-any`, and the plugins `pydantic.mypy` and `returns.contrib.mypy.returns_plugin`.

#### Scenario: A function returns Any

- GIVEN a module that declares a parameter as `Any`
- WHEN the commit hook runs mypy
- THEN mypy reports `explicit-any`, and the commit fails

Verify: `pre-commit run mypy --all-files`

### `typing:a-fallible-operation-returns-a-result` — A fallible operation returns a Result

When an operation can fail, the function MUST return `Result[T, E]` from `returns`, where `E` is a typed error of the domain, and MUST NOT raise the failure to its caller.

#### Scenario: A sensor read fails

- GIVEN a collector whose source raises `PermissionError`
- WHEN the collector runs
- THEN it returns a `Failure` that holds a `CollectorError` of the kind `permission-denied`, and no exception leaves the collector

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `typing:a-match-lists-every-case` — A match lists every case

When code matches on a `Result` or on a `StrEnum`, the `match` MUST list every case, and a `match` on a `Result` MUST match `outcome(result)` from `vitals.domain.outcome`, the union `Success[T] | Failure[E]`, so mypy proves the match exhaustive through `exhaustive-match`.

#### Scenario: A new error kind

- GIVEN a `match` on `outcome(snapshot.gpu)` that lists only `case Success(gpu)`
- WHEN the commit hook runs mypy
- THEN mypy reports `exhaustive-match` for the unhandled `Failure` case

Verify: `pre-commit run mypy --all-files`

### `typing:pydantic-owns-every-boundary` — pydantic owns every boundary

Where outside data enters the program, from the configuration file, the environment, or the command line, a pydantic model with `frozen=True` and `extra="forbid"` MUST validate it.

#### Scenario: An unknown key in the configuration file

- GIVEN a `config.toml` that holds the key `refresh`, which the model does not declare
- WHEN `vitals` loads its configuration
- THEN validation fails and names the key and the file

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `typing:a-frozen-dataclass-owns-every-internal-value` — A frozen dataclass owns every internal value

An internal value that crosses a module boundary, such as a sample, a snapshot, or a panel state, MUST be a dataclass with `frozen=True`, `slots=True`, and `kw_only=True`, and MUST NOT be a `dict` keyed by strings.

#### Scenario: A collector returns its sample

- GIVEN the memory collector
- WHEN it reads the source
- THEN it returns a `MemorySample` dataclass, and assigning one of its fields raises `FrozenInstanceError`

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `typing:a-unit-is-a-newtype` — A unit is a NewType, and a closed set is a StrEnum

A quantity with a unit MUST carry a `NewType` of that unit, such as `Percent`, `Celsius`, `Bytes`, `Watts`, `Seconds`, or `Megahertz`, and a closed set of names MUST be an `enum.StrEnum`.

#### Scenario: Bytes passed where a percent is expected

- GIVEN a gauge that takes a `Percent`
- WHEN a caller passes a `Bytes` value
- THEN mypy reports `arg-type`

Verify: `pre-commit run mypy --all-files`

### `typing:an-untyped-library-enters-through-one-adapter` — An untyped library enters through one adapter

Where a library ships no types, one adapter module MUST import it, wrap each call with `@safe` from `returns`, and expose a typed facade, and every `# type: ignore` MUST name its error code.

#### Scenario: The NVML import

- GIVEN `pynvml`, which ships no type information
- WHEN mypy checks the project
- THEN only `vitals.adapters.nvml_source` imports `pynvml`, and its one ignore names its code

Verify: `pre-commit run mypy --all-files`

### `typing:ruff-selects-every-rule-family` — ruff selects every rule family

The lint MUST select every ruff rule family, and its ignore list MUST hold only a rule that conflicts with `ruff format`, a rule that excludes another selected rule, or a rule this spec rejects by name, each with its reason in a comment.

#### Scenario: A new rule family in a ruff release

- GIVEN `select = ["ALL"]`
- WHEN a ruff update adds a rule family
- THEN the lint applies it with no edit to the configuration

Verify: `pre-commit run ruff-check --all-files`

## Unenforced

| Rule                                           | Reviewer confirms                                                                                                                                                                                                                                       |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `typing:ruff-selects-every-rule-family`        | each entry of the ignore list carries its reason. The rules this spec rejects by name are `CPY001`, because the root `LICENSE` covers every file, and, in `tests/` only, `S101` and `PLR2004`, because pytest asserts with `assert` and inline numbers. |
| `typing:a-fallible-operation-returns-a-result` | `@safe` appears only in an adapter module, and the one place that turns a `Failure` into an exit code is `main`.                                                                                                                                        |
