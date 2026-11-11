# Dashboard Specification

<!--TOC-->

- [Purpose](#purpose)
- [Requirements](#requirements)
  - [`dashboard:every-panel-carries-a-title` — Every panel carries a title](#dashboardevery-panel-carries-a-title--every-panel-carries-a-title)
  - [`dashboard:the-overview-shows-the-vital-signs` — The overview shows the vital signs](#dashboardthe-overview-shows-the-vital-signs--the-overview-shows-the-vital-signs)
  - [`dashboard:no-panel-shows-a-value-per-core` — No panel shows a value per core](#dashboardno-panel-shows-a-value-per-core--no-panel-shows-a-value-per-core)
  - [`dashboard:a-failed-source-shows-its-kind` — A failed source shows its error kind](#dashboarda-failed-source-shows-its-kind--a-failed-source-shows-its-error-kind)
  - [`dashboard:the-chart-shows-five-minutes-of-temperatures` — The chart shows five minutes of temperatures](#dashboardthe-chart-shows-five-minutes-of-temperatures--the-chart-shows-five-minutes-of-temperatures)
  - [`dashboard:the-processes-view-ranks-processes` — The processes view ranks processes](#dashboardthe-processes-view-ranks-processes--the-processes-view-ranks-processes)
  - [`dashboard:one-registry-maps-the-views-to-keys` — One registry maps the views to keys](#dashboardone-registry-maps-the-views-to-keys--one-registry-maps-the-views-to-keys)
  - [`dashboard:sampling-runs-off-the-event-loop` — Sampling runs off the event loop](#dashboardsampling-runs-off-the-event-loop--sampling-runs-off-the-event-loop)
  - [`dashboard:a-theme-recolors-every-panel` — A theme recolors every panel](#dashboarda-theme-recolors-every-panel--a-theme-recolors-every-panel)
- [Unenforced](#unenforced)

<!--TOC-->

## Purpose

This domain covers what the Textual app of `vitals` draws and how it reacts: the views, the panels of each view, their titles, labels, and units, the temperature chart, the key bindings, the theme, and the refresh. The dashboard holds no system call: it draws the `Snapshot` values that the collectors build. How the command line starts the app belongs to the CLI spec.

## Requirements

### `dashboard:every-panel-carries-a-title` — Every panel carries a title

Every panel MUST be a container whose `border_title` names its subject, and every value in it MUST carry a label and its unit.

#### Scenario: The memory panel

- GIVEN a snapshot with 12.4 GiB used of 31.0 GiB
- WHEN the overview draws
- THEN the panel titled `Memory` shows the label `Used`, the number, and `GiB` beside a gauge at 40 percent

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `dashboard:the-overview-shows-the-vital-signs` — The overview shows the vital signs

The overview view MUST show these panels: `CPU` with one gauge of the aggregate usage, the package temperature, the frequency, and the load average; `GPU` with the utilization, the VRAM used of total, the temperature, and the power draw; `Memory` and `Swap`, each with one gauge of used of total; `Disks` with one bar for each device, labeled with its mount point, used, and total; and `Temperatures` with the chart, under a header that shows the host name and the uptime and over a footer that shows the key bindings.

#### Scenario: The first draw on a populated host

- GIVEN a fake snapshot where every source succeeds
- WHEN the app opens at a terminal of 120 columns and 40 rows
- THEN the screen matches the recorded snapshot of the overview, with all six panel titles

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `dashboard:no-panel-shows-a-value-per-core` — No panel shows a value per core

The CPU panel MUST show the aggregate usage alone, and MUST NOT draw a grid, a bar, or a number for each core.

#### Scenario: A host with 22 logical CPUs

- GIVEN a snapshot from a host with 22 logical CPUs
- WHEN the overview draws
- THEN the CPU panel holds exactly one gauge

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `dashboard:a-failed-source-shows-its-kind` — A failed source shows its error kind

If the `Result` of a source is a `Failure`, then its panel MUST show the error kind and its detail in place of the values, and the app MUST keep running and drawing every other panel.

#### Scenario: No NVIDIA driver

- GIVEN a snapshot whose GPU result is a `Failure` of the kind `source-unavailable`
- WHEN the overview draws
- THEN the `GPU` panel shows `source-unavailable` and its detail, and the other five panels show their values

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `dashboard:the-chart-shows-five-minutes-of-temperatures` — The chart shows five minutes of temperatures

The `Temperatures` panel MUST draw a line chart of the last five minutes with one series each for the CPU package, the GPU, and the NVMe drive, a legend that names each series, and an axis in degrees Celsius.

#### Scenario: The NVMe sensor is missing

- GIVEN a history where the NVMe series holds no sample
- WHEN the chart draws
- THEN it draws the CPU and GPU series, and the legend omits the NVMe series

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `dashboard:the-processes-view-ranks-processes` — The processes view ranks processes

The processes view MUST show two read-only tables, `Top CPU` and `Top memory`, with the PID, the name, the user, the CPU percent, and the resident memory of each process, under the same title and label rules as the overview.

#### Scenario: Switching to the processes view

- GIVEN the app on the overview
- WHEN the user presses `2`
- THEN the processes view opens with both tables titled

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `dashboard:one-registry-maps-the-views-to-keys` — One registry maps the views to keys

The app MUST take its views from one registry that maps a name and a key from `1` to `9` to a screen, and MUST bind `q` to quit, `?` to the help screen, and `ctrl+p` to the command palette.

#### Scenario: A view name from the command line

- GIVEN the registry entries `overview` on `1` and `processes` on `2`
- WHEN the app starts with the view `processes`
- THEN the processes view opens first, and `1` returns to the overview

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `dashboard:sampling-runs-off-the-event-loop` — Sampling runs off the event loop

The app MUST build each `Snapshot` on a worker thread at the configured interval, 2 seconds by default, and post it to the app as a message, and a widget MUST NOT call a collector.

#### Scenario: A slow source

- GIVEN a fake source that takes one second to answer
- WHEN the app runs
- THEN the key bindings answer while the worker waits

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `dashboard:a-theme-recolors-every-panel` — A theme recolors every panel

The colors MUST come from the design tokens of the active Textual theme in `vitals.tcss`, so a theme picked from the command palette recolors every panel, and a Python module MUST NOT set a color.

#### Scenario: Another theme from the palette

- GIVEN the app with its default theme
- WHEN the user picks another theme from the command palette
- THEN every panel border and gauge takes the colors of the new theme

Verify: `pre-commit run pytest --hook-stage manual --all-files`

## Unenforced

| Rule                                           | Reviewer confirms                                                                                          |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `dashboard:the-overview-shows-the-vital-signs` | the operator judged the overview on tumblesuse before its snapshot was recorded.                           |
| `dashboard:a-theme-recolors-every-panel`       | no `color`, `background`, or `Style` with a fixed color appears in `src/vitals/ui/` outside `vitals.tcss`. |
