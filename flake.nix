{
  description = "vitals: a terminal dashboard of the machine's vital signs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    # The docs gate of the repository (sdd). The tag in the URL is the
    # version, and flake.lock pins its content. The `sdd self-depend sync`
    # line of .envrc moves both. Run `sdd upgrade` when the new release moves
    # the canon.
    spec-driven-docs = {
      url = "github:gubasso/spec-driven-docs/v0.15.1";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # The branch workflow of the repository (rk): worktrees, local squash
    # integration, and an external release. The tag in the URL is the
    # version, and flake.lock pins its content. The `rk self-depend sync`
    # line of .envrc moves both. Run `rk upgrade` when the new release moves
    # the landed files.
    release-kit = {
      url = "github:gubasso/release-kit/v0.9.8";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.spec-driven-docs.follows = "spec-driven-docs";
    };

    # The package build reads uv.lock, so the flake holds no Python library of
    # its own: pyproject.toml and uv.lock own them. Template:
    # https://github.com/pyproject-nix/uv2nix/blob/master/templates/hello-world/flake.nix
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      release-kit,
      spec-driven-docs,
      ...
    }:
    let
      # The one supported system (exobrain-tech
      # project-platform:one-supported-system).
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      # .python-version names the exact interpreter. The host's uv installs it
      # for development, and the package builds on the nixpkgs Python of the
      # same patch, so development and the shipped program run one interpreter.
      pythonVersion = pkgs.lib.fileContents ./.python-version;
      python =
        pkgs."python${pkgs.lib.concatStrings (pkgs.lib.take 2 (pkgs.lib.splitVersion pythonVersion))}";

      # The Python libraries of uv.lock, as wheels, built on that interpreter.
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
      pythonSet = (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
        pkgs.lib.composeManyExtensions [
          pyproject-build-systems.overlays.wheel
          (workspace.mkPyprojectOverlay { sourcePreference = "wheel"; })
        ]
      );
      venv = pythonSet.mkVirtualEnv "vitals-env" workspace.deps.default;

      # The package exposes bin/vitals alone, so a profile that installs it
      # gets no python and no script of a library on its PATH.
      inherit (pkgs.callPackages pyproject-nix.build.util { }) mkApplication;
      vitals = mkApplication {
        inherit venv;
        package = pythonSet.vitals;
      };

      # The nixpkgs virtualenv imports `packaging` but does not declare it, so
      # it runs only while PYTHONPATH carries the libraries of pre-commit, and
      # that PYTHONPATH would shadow the packages of the project venv. Declaring
      # the dependency lets pre-commit build its Python hook environments with
      # PYTHONPATH unset. The fix holds on nixpkgs master of 2026-11-11. The
      # rebuilt virtualenv skips its test suite, which the hooks of this
      # repository replace.
      pre-commit = pkgs.pre-commit.override {
        python3Packages = pkgs.python3Packages.overrideScope (
          _final: prev: {
            virtualenv = prev.virtualenv.overridePythonAttrs (old: {
              dependencies = (old.dependencies or [ ]) ++ [ prev.packaging ];
              doCheck = false;
            });
          }
        );
      };
    in
    {
      formatter.${system} = pkgs.nixfmt;

      # The packaged program: `nix run github:gubasso/vitals/<tag>`. It carries
      # no host path; the launcher of each host puts the directory of
      # libnvidia-ml.so.1 on LD_LIBRARY_PATH (SPEC-collectors).
      packages.${system}.default = vitals;

      apps.${system}.default = {
        type = "app";
        program = "${vitals}/bin/vitals";
        meta.description = "A terminal dashboard of the machine's vital signs";
      };

      # The host supplies uv, and uv owns the Python interpreter, so the
      # devshell holds only the project tools.
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          # The hook runner and the command surface.
          pre-commit
          pkgs.just
          # The formatter of Markdown (dprint hook) and of Nix (nixfmt hook).
          pkgs.dprint
          pkgs.nixfmt
          # The runtime on which pre-commit builds the node hook of
          # markdownlint-cli2: the generic node that pre-commit downloads does
          # not run on a host without the standard glibc loader.
          pkgs.nodejs
          # rk, the branch workflow: `rk worktree add`, `rk integrate`, and
          # the rk hooks.
          release-kit.packages.${system}.default
          # sdd, the docs gate: its hooks, `sdd verify`, and `sdd status`.
          spec-driven-docs.packages.${system}.default
        ];

        # The Python setup hook exports the libraries of pkgs.pre-commit, built
        # for the nixpkgs Python, on PYTHONPATH. pre-commit finds them through
        # its own wrapper, and the variable would shadow the packages of the
        # project venv, which runs another Python. So the shell drops it.
        shellHook = ''
          unset PYTHONPATH
        '';
      };

      checks.${system} = {
        # The package builds, and its vitals answers --once on the fixed fakes.
        package-runs-once = pkgs.runCommand "vitals-runs-once" { } ''
          export HOME="$TMPDIR"
          VITALS_FAKE_SOURCES=1 ${vitals}/bin/vitals --once > "$TMPDIR/snapshot.json"
          ${pkgs.jq}/bin/jq -e '.gpu.temperature == 52.0' "$TMPDIR/snapshot.json" > /dev/null
          touch "$out"
        '';

        # Fails when nixpkgs ships another patch than .python-version names.
        python-version = pkgs.runCommand "python-version-is-aligned" { } ''
          if [ "${python.version}" != "${pythonVersion}" ]; then
            echo "nixpkgs ships Python ${python.version}, and .python-version names ${pythonVersion}" >&2
            exit 1
          fi
          touch "$out"
        '';
      };
    };
}
