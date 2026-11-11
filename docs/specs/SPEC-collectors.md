# Collectors Specification

<!--TOC-->

- [Purpose](#purpose)
- [Requirements](#requirements)
  - [`collectors:a-collector-returns-a-result` — A collector returns a Result](#collectorsa-collector-returns-a-result--a-collector-returns-a-result)
  - [`collectors:one-collector-per-source` — One collector reads each source](#collectorsone-collector-per-source--one-collector-reads-each-source)
  - [`collectors:error-kinds-are-a-closed-set` — The error kinds are a closed set](#collectorserror-kinds-are-a-closed-set--the-error-kinds-are-a-closed-set)
  - [`collectors:one-adapter-holds-each-library` — One adapter holds each system library](#collectorsone-adapter-holds-each-library--one-adapter-holds-each-system-library)
  - [`collectors:the-cpu-sample-is-aggregate` — The CPU sample is aggregate](#collectorsthe-cpu-sample-is-aggregate--the-cpu-sample-is-aggregate)
  - [`collectors:mounts-collapse-by-device` — Mounts collapse by block device](#collectorsmounts-collapse-by-device--mounts-collapse-by-block-device)
  - [`collectors:the-gpu-reads-nvml-at-runtime` — The GPU collector reads NVML at runtime](#collectorsthe-gpu-reads-nvml-at-runtime--the-gpu-collector-reads-nvml-at-runtime)
  - [`collectors:processes-are-ranked-by-cpu-and-memory` — The processes are ranked by CPU and by memory](#collectorsprocesses-are-ranked-by-cpu-and-memory--the-processes-are-ranked-by-cpu-and-by-memory)
  - [`collectors:history-keeps-a-fixed-window` — The history keeps a fixed window](#collectorshistory-keeps-a-fixed-window--the-history-keeps-a-fixed-window)
- [Unenforced](#unenforced)

<!--TOC-->

## Purpose

This domain covers how `vitals` reads the state of the machine: one collector for each data source, the typed samples they return, the closed set of error kinds, the adapters that hold the system libraries, and the history that feeds the temperature chart. A collector holds no UI code. How the dashboard draws a sample belongs to the dashboard spec, and how the command line prints one belongs to the CLI spec.

## Requirements

### `collectors:a-collector-returns-a-result` — A collector returns a Result

A collector MUST be a function of its adapter that returns `Result[Sample, CollectorError]`, and MUST turn every failure of its source into a `Failure`.

#### Scenario: The source raises

- GIVEN a fake adapter whose read raises `OSError`
- WHEN the collector runs
- THEN it returns `Failure(CollectorError(kind=source-unavailable))`, and the test sees no exception

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `collectors:one-collector-per-source` — One collector reads each source

The program MUST hold one collector for each source: the host name and uptime, the CPU, the memory and the swap, the disks, the temperatures, the GPU, and the processes, and a `Snapshot` MUST hold one `Result` for each of them.

#### Scenario: The GPU source fails and the rest succeed

- GIVEN fakes where only the GPU adapter fails
- WHEN the program builds a `Snapshot`
- THEN the snapshot holds a `Failure` for the GPU and a `Success` for each other source

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `collectors:error-kinds-are-a-closed-set` — The error kinds are a closed set

A `CollectorError` MUST carry a kind from the `StrEnum` `CollectorErrorKind`, whose members are `source-unavailable`, `permission-denied`, `no-device`, and `unsupported`, and a human-readable detail.

#### Scenario: The NVIDIA driver is absent

- GIVEN a host where `libnvidia-ml.so.1` does not load
- WHEN the GPU collector runs
- THEN it returns a `Failure` of the kind `source-unavailable`

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `collectors:one-adapter-holds-each-library` — One adapter holds each system library

The module `vitals.adapters.psutil_source` MUST be the only importer of `psutil`, and `vitals.adapters.nvml_source` MUST be the only importer of `pynvml`, from the distribution `nvidia-ml-py`, and each collector MUST depend on a `typing.Protocol` of its adapter, so a test passes a fake.

#### Scenario: A collector imports psutil

- GIVEN `vitals/collectors/cpu.py` with `import psutil`
- WHEN the test suite runs
- THEN the import-boundary test fails and names the module

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `collectors:the-cpu-sample-is-aggregate` — The CPU sample is aggregate

The CPU collector MUST return the aggregate usage in percent, the package temperature, the current frequency, and the load average of 1, 5, and 15 minutes, and MUST NOT return a value per core.

#### Scenario: A host with 22 logical CPUs

- GIVEN a fake adapter that reports 22 per-core usages and an aggregate of 37 percent
- WHEN the CPU collector runs
- THEN the sample holds the one value 37 percent and no list of cores

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `collectors:mounts-collapse-by-device` — Mounts collapse by block device

The disk collector MUST return one sample for each block device that holds a mounted physical filesystem, labeled with its shortest mount point, and MUST skip a pseudo filesystem such as `tmpfs`, `proc`, or `overlay`.

#### Scenario: Subvolumes of one btrfs device

- GIVEN the mounts `/`, `/home`, `/var`, and `/opt` on `/dev/nvme0n1p2`, `/boot/efi` on `/dev/nvme0n1p1`, and `/run/media/gbasso/data` on `/dev/sda1`
- WHEN the disk collector runs
- THEN it returns three samples, labeled `/`, `/boot/efi`, and `/run/media/gbasso/data`

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `collectors:the-gpu-reads-nvml-at-runtime` — The GPU collector reads NVML at runtime

The GPU collector MUST load `libnvidia-ml.so.1` through `pynvml` when it first runs, and MUST report the utilization, the VRAM used and total, the temperature, and the power draw of the first NVIDIA device.

#### Scenario: The library path of the host

- GIVEN a host whose launcher puts the directory of `libnvidia-ml.so.1` on `LD_LIBRARY_PATH`
- WHEN the GPU collector runs
- THEN it returns a `GpuSample` with the device name and all four values

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `collectors:processes-are-ranked-by-cpu-and-memory` — The processes are ranked by CPU and by memory

The processes collector MUST return the top processes by CPU usage and the top processes by resident memory, each entry with its PID, its name, its user, its CPU percent, and its resident bytes, and MUST skip a process that exits during the read.

#### Scenario: A process exits during the read

- GIVEN a fake adapter where one process raises `NoSuchProcess` while its values are read
- WHEN the processes collector runs
- THEN it returns a `Success` without that process

Verify: `pre-commit run pytest --hook-stage manual --all-files`

### `collectors:history-keeps-a-fixed-window` — The history keeps a fixed window

The temperature history MUST keep the samples of the last five minutes in a ring of fixed length, the window divided by the sampling interval, and MUST drop the oldest sample when it is full.

#### Scenario: A full ring at a 2-second interval

- GIVEN a history of 150 samples at a 2-second interval
- WHEN one more sample arrives
- THEN the history still holds 150 samples, and the oldest one is gone

Verify: `pre-commit run pytest --hook-stage manual --all-files`

## Unenforced

| Rule                                       | Reviewer confirms                                                                                                                                                                                      |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `collectors:the-gpu-reads-nvml-at-runtime` | the packaged program carries no host path. The launcher of each host, a nix-secrets app, sets the library path: `/usr/lib64` on a standalone Home Manager host, and `/run/opengl-driver/lib` on NixOS. |
| `collectors:the-gpu-reads-nvml-at-runtime` | a test marked `host`, which the default run skips, reads every source of the real machine once.                                                                                                        |
