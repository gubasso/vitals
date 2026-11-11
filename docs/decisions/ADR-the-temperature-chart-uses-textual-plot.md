# The temperature chart uses textual-plot

## Context and Problem Statement

The Temperatures panel draws three series over five minutes, with a legend and an axis in degrees. Two Textual chart widgets exist, and the chart must pass the typing contract and recolor with the theme like every other panel.

## Considered Options

- `textual-plot` — chosen.
- `textual-plotext` — rejected: its `Plot` inherits the untyped plotext figure, so every call returns an implicit `Any`, and its fixed colors ignore the theme.

## Decision Outcome

Chosen option: `textual-plot` — a spike on 2026-11-11 drew the same three series with both widgets, and textual-plot won on the typing gate and on the picture. Sources: [textual-plot](https://github.com/davidfokkema/textual-plot), [textual-plotext](https://github.com/Textualize/textual-plotext).

- textual-plot 0.10.1 types its whole API, and mypy strict with `explicit-any` passes on the widget.
- It draws braille lines, round axis ticks, and a boxed legend. textual-plotext drew its legend over the data and placed the axis label under the chart.
- Each series takes its color from a token of the active theme, so the palette's theme switch recolors the chart. The chart passes the token to Rich, which names an ANSI color without the `ansi_` prefix that Textual uses.
- The chart pads its y limits by 2 °C, so a series at the lowest or the highest value does not lie on an axis.

Enforced by `dashboard:the-chart-shows-five-minutes-of-temperatures` and `dashboard:a-theme-recolors-every-panel`.

## Consequences

- Good: the chart meets the typing contract with no facade of its own.
- Good: one theme colors the gauges, the borders, and the chart.
- Bad: textual-plot brings numpy, a large dependency for one chart.

## Status

Accepted.
