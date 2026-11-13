# vitals task runner. Every recipe runs in the flake devShell: in a shell that
# direnv activated, or as `direnv exec . just <recipe>`.

# The host tools of every recipe, checked once before any recipe runs. The list
# lives in host-requirements.toml, and exobrain from the devShell reads it
# (https://github.com/gubasso/exobrain-tech/blob/v1.1.0/programming/project-bootstrap/03-local-dev-environment.md#host-requirements).
# A recipe that alone uses a host tool checks it as its first line.
_host := shell("exobrain host-check git uv")

# List the recipes.
default:
	@just --list

# Install the git hooks of every stage.
hooks-install:
	exobrain host-check prek
	prek install

# Format Python, Markdown, and Nix through their hooks.
fmt:
	exobrain host-check prek
	-prek run ruff-format --all-files
	-prek run dprint --all-files
	-prek run nixfmt --all-files

# The fast checks: the pre-commit stage on every file.
lint:
	exobrain host-check prek
	prek run --all-files

# The strict type check, through its hook.
typecheck:
	exobrain host-check prek
	prek run mypy --all-files

# The test suite.
test:
	uv run --frozen pytest

# Every check, once: the manual stage is the union of the pre-commit and the
# pre-push hooks. A green check is a green push.
check:
	exobrain host-check prek nix
	prek run --all-files --hook-stage manual

# Start the dashboard.
run *args:
	uv run --frozen vitals {{args}}
