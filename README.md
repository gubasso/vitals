# vitals

A terminal dashboard of the machine's vital signs: CPU, GPU, memory, swap, disks, and temperatures.

## Run

```bash
nix run github:gubasso/vitals
```

From a checkout, run `just run`. `vitals --help` lists the flags, and `vitals --once` prints one reading as JSON.

## Configure

vitals reads `${XDG_CONFIG_HOME:-~/.config}/vitals/config.toml`. Every key is optional:

```toml
view = "overview"      # the view that opens first: overview or processes
interval = 2.0         # the sampling interval, in seconds
theme = "textual-dark" # a Textual theme; ctrl+p then "theme" lists them
```

A `VITALS_<KEY>` variable overrides the file, and a flag such as `--theme nord` overrides both. The log goes to `${XDG_STATE_HOME:-~/.local/state}/vitals/vitals.log`.

## Develop

The host needs `nix`, `direnv`, `git`, and `uv`. On entry, direnv loads the flake devshell and syncs the venv from `uv.lock` with the Python of `.python-version`.

```bash
direnv allow
just hooks-install
just check
```

`just` lists the other recipes.

## Documentation

- `AGENTS.md`: the rules of the repository, for people and agents.
- `docs/specs/`: what the program does, one spec per domain.
- `docs/decisions/`: why the program is built the way it is.

## License

MIT. See `LICENSE`.
