# The UI framework is Textual

## Context and Problem Statement

`vitals` draws a live dashboard in a terminal: titled panels, labeled gauges, bars, a line chart, and more than one view. bottom 0.15 and btop 1.4.8 both failed this brief on 2026-11-11, because their layouts and labels are fixed. The program needs a framework that gives each panel a title, each value a label, and the user a theme.

## Considered Options

- `Textual` — chosen.
- `rich with Live` — rejected: it redraws printed output and has no screens, no key bindings, and no widgets to compose.
- `curses` — rejected: every panel, border, and gauge would be drawn by hand, and nothing tests a screen.
- `A Rust TUI framework` — rejected: the typing contract and the data libraries of this project are Python.

## Decision Outcome

Chosen option: `Textual` — it is the most used Python TUI framework, and live dashboards such as dolphie already build on it.

- Textual 8.2.8 (2026-06-30) gives a border title on every container, `ProgressBar`, `Sparkline`, `Header`, `Footer`, screens, themes, and a command palette. Source: [Textual](https://github.com/Textualize/textual).
- dolphie, posting, and harlequin show the project shape: screens, `.tcss` stylesheets, and snapshot tests. Source: [dolphie pyproject](https://github.com/charles-001/dolphie/blob/main/pyproject.toml).
- `pytest-textual-snapshot` records each view as an SVG and fails on a changed screen.

Enforced by `dashboard:every-panel-carries-a-title` and `dashboard:a-theme-recolors-every-panel`.

## Consequences

- Good: a panel is a widget with a title, and a theme recolors every panel with no code.
- Good: a view is a screen in one registry, so a later view is one entry.
- Bad: Textual brings its own event loop, so sampling must run on a worker.

## Status

Accepted.
