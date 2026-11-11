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

      # .python-version names the exact interpreter. The host's uv installs it
      # for development, and the package builds on the nixpkgs Python of the
      # same patch, so development and the shipped program run one interpreter.
      pythonVersion = pkgs.lib.fileContents ./.python-version;
      python =
        pkgs."python${pkgs.lib.concatStrings (pkgs.lib.take 2 (pkgs.lib.splitVersion pythonVersion))}";
    in
    {
      # The host supplies uv, and uv owns the Python interpreter, so the
      # devshell holds only the project tools.
      devShells.${system}.default = pkgs.mkShell {
        packages = [ ];
      };

      # Fails when nixpkgs ships another patch than .python-version names.
      checks.${system}.python-version = pkgs.runCommand "python-version-is-aligned" { } ''
        if [ "${python.version}" != "${pythonVersion}" ]; then
          echo "nixpkgs ships Python ${python.version}, and .python-version names ${pythonVersion}" >&2
          exit 1
        fi
        touch "$out"
      '';
    };
}
