# CLI Specification

<!--TOC-->

- [Purpose](#purpose)
- [Requirements](#requirements)
  - [`cli:main-is-the-one-exit-boundary` — main is the one exit boundary](#climain-is-the-one-exit-boundary--main-is-the-one-exit-boundary)
  - [`cli:the-exit-codes-follow-sysexits` — The exit codes follow sysexits](#clithe-exit-codes-follow-sysexits--the-exit-codes-follow-sysexits)
  - [`cli:the-flags-select-the-run` — The flags select the run](#clithe-flags-select-the-run--the-flags-select-the-run)
  - [`cli:once-prints-one-snapshot-as-json` — once prints one snapshot as JSON](#clionce-prints-one-snapshot-as-json--once-prints-one-snapshot-as-json)
  - [`cli:flags-win-over-environment-over-file` — Flags win over the environment, which wins over the file](#cliflags-win-over-environment-over-file--flags-win-over-the-environment-which-wins-over-the-file)
  - [`cli:a-configuration-error-names-its-layer` — A configuration error names its layer](#clia-configuration-error-names-its-layer--a-configuration-error-names-its-layer)
  - [`cli:the-configuration-file-follows-xdg` — The configuration file follows XDG](#clithe-configuration-file-follows-xdg--the-configuration-file-follows-xdg)
  - [`cli:logs-go-to-a-file-only` — Logs go to a file only](#clilogs-go-to-a-file-only--logs-go-to-a-file-only)
- [Unenforced](#unenforced)

<!--TOC-->

## Purpose

This domain covers the command line of `vitals`: its flags, its exit codes, its configuration and the precedence of its layers, its log file, and the one boundary that turns a failure into an exit code. It adapts the CLI design and the Python CLI chapters of exobrain-tech to a full-screen terminal app. What the app draws belongs to the dashboard spec.

## Requirements

### `cli:main-is-the-one-exit-boundary` — main is the one exit boundary

The function `main` MUST match the `Result` of the run, print the message of a `Failure` to stderr, and exit with the sysexits code of its kind, and no other function MUST call `sys.exit` or raise `SystemExit`.

#### Scenario: A malformed configuration file

- GIVEN a `config.toml` that is not valid TOML
- WHEN the user runs `vitals`
- THEN stderr names the file path and the parse error, and the exit code is 78

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `cli:the-exit-codes-follow-sysexits` — The exit codes follow sysexits

The command MUST exit 0 on success, 64 on a usage error, 69 when no source of the machine can be read, 70 on an internal error, and 78 on a configuration error, as BSD `sysexits.h` defines them.

#### Scenario: An unknown view

- GIVEN the registry with the views `overview` and `processes`
- WHEN the user runs `vitals --view network`
- THEN stderr lists the known views, and the exit code is 64

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `cli:the-flags-select-the-run` — The flags select the run

The command MUST accept `--view NAME`, `--interval SECONDS`, `--theme NAME`, `--once`, `--version`, and `--help`, and `--help` MUST list every view of the registry.

#### Scenario: The help text

- GIVEN the installed command
- WHEN the user runs `vitals --help`
- THEN stdout names each flag and the views `overview` and `processes`, and the exit code is 0

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `cli:once-prints-one-snapshot-as-json` — once prints one snapshot as JSON

When the user passes `--once`, the command MUST build one `Snapshot`, print it as one JSON object on stdout, with a `Failure` as an object that holds its kind and detail, and exit without starting the app.

#### Scenario: A script reads the GPU temperature

- GIVEN a host where every source succeeds
- WHEN a script runs `vitals --once`
- THEN stdout parses as JSON, and the key `gpu` holds the temperature in degrees Celsius

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `cli:flags-win-over-environment-over-file` — Flags win over the environment, which wins over the file

The configuration MUST resolve each setting from the flag first, then the `VITALS_` environment variable, then `config.toml`, then the default, and the model MUST be frozen and forbid unknown keys.

#### Scenario: The interval in three layers

- GIVEN `interval = 5` in `config.toml` and `VITALS_INTERVAL=3` in the environment
- WHEN the user runs `vitals --interval 1`
- THEN the app samples every second

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `cli:a-configuration-error-names-its-layer` — A configuration error names its layer

If a setting fails validation, then the message MUST name the layer that supplied it, the flag, the variable, or the file path, and the setting.

#### Scenario: A negative interval in the environment

- GIVEN `VITALS_INTERVAL=-1`
- WHEN the user runs `vitals`
- THEN stderr names `VITALS_INTERVAL` and the rule it breaks, and the exit code is 78

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `cli:the-configuration-file-follows-xdg` — The configuration file follows XDG

The command MUST read its configuration from `${XDG_CONFIG_HOME:-$HOME/.config}/vitals/config.toml` and run on the defaults when the file is absent.

#### Scenario: No configuration file

- GIVEN a home with no `vitals` configuration folder
- WHEN the user runs `vitals --once`
- THEN the command runs on the defaults and exits 0

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `cli:logs-go-to-a-file-only` — Logs go to a file only

The command MUST write its log to `${XDG_STATE_HOME:-$HOME/.local/state}/vitals/vitals.log`, and while the app runs, a log line MUST NOT reach stdout or stderr, because the app owns the screen.

#### Scenario: A collector warning while the app runs

- GIVEN the app running with a source that fails
- WHEN the collector logs a warning
- THEN the line appears in `vitals.log` and nowhere on the screen

Verify: `pre-commit run pytest --hook-stage manual --all-files`

## Unenforced

| Rule                                | Reviewer confirms                                         |
| ----------------------------------- | --------------------------------------------------------- |
| `cli:main-is-the-one-exit-boundary` | `grep -rn "sys.exit\|SystemExit" src/` finds only `main`. |
