{
  description = "vitals: a terminal dashboard of the machine's vital signs";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      # The one supported system (exobrain-tech
      # project-platform:one-supported-system).
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      # The one declared Python version. Keep it within requires-python of
      # pyproject.toml and equal to .python-version.
      python = pkgs.python315;
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          python
          pkgs.uv
        ];

        # Precompiled manylinux wheels that uv installs, such as pydantic-core,
        # link against libstdc++.so.6 and libz.so.1, which Nix keeps off the
        # default loader path.
        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
          pkgs.stdenv.cc.cc.lib
          pkgs.zlib
        ];

        # Hand the pinned interpreter to uv, forbid interpreter downloads,
        # install uv.lock into .venv as it is, and put .venv/bin on PATH.
        # Messages go to stderr, because `nix develop --command` and
        # `direnv exec` share stdout with the command. After a change of
        # pyproject.toml, run `uv lock`, then `direnv reload`.
        shellHook = ''
          root="$(git rev-parse --show-toplevel)"
          export UV_PYTHON="${python}/bin/python3"
          export UV_PYTHON_DOWNLOADS=never
          export UV_PROJECT_ENVIRONMENT="$root/.venv"
          uv sync --frozen --quiet --project "$root" \
            || echo "uv sync failed: after a change of pyproject.toml, run uv lock" >&2
          export VIRTUAL_ENV="$root/.venv"
          export PATH="$root/.venv/bin:$PATH"
        '';
      };
    };
}
