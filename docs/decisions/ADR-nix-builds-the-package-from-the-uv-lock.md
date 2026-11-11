# Nix builds the package from uv.lock with uv2nix

## Context and Problem Statement

nix-secrets installs `vitals` on every host as a flake input pinned to a release tag. The package must run the libraries of `uv.lock` on the interpreter patch of `.python-version`, and the flake must not hold a second list of Python libraries.

## Considered Options

- `uv2nix from uv.lock` — chosen.
- `buildPythonApplication with nixpkgs Python packages` — rejected: the flake would hold a second dependency list, and nixpkgs pins its own versions of each library.
- `A PyPI release installed with uv tool` — deferred: revisit when a consumer outside Nix asks for it.

## Decision Outcome

Chosen option: `uv2nix from uv.lock` — it reads the lock, so the lock stays the one owner of every library. Sources: [uv2nix](https://github.com/pyproject-nix/uv2nix), [uv2nix docs](https://pyproject-nix.github.io/uv2nix/).

- The flake adds `uv2nix`, `pyproject-nix`, and `pyproject-build-systems`, and builds `packages.x86_64-linux.default` and the app.
- The package builds on the nixpkgs Python of the exact patch in `.python-version`. A flake check fails when nixpkgs ships another patch, so the shipped program and the uv-managed venv run one interpreter.
- The package carries no host path. The launcher of each host sets the path of the NVIDIA library.

Enforced by `collectors:the-gpu-reads-nvml-at-runtime`.

## Consequences

- Good: `nix run github:gubasso/vitals/<tag>` runs the released program, and nix-secrets pins it like any other input.
- Good: a lock update reaches the package with no edit to the flake.
- Bad: a library with a native build that uv2nix cannot resolve from a wheel needs an override in the flake.

## Status

Accepted.
