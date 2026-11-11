# vitals task runner. Every recipe runs in the flake devShell: in a shell that
# direnv activated, or as `direnv exec . just <recipe>`.

# List the recipes.
default:
	@just --list

# Install the git hooks of every stage.
hooks-install:
	pre-commit install

# Format Python, Markdown, and Nix through their hooks.
fmt:
	-pre-commit run ruff-format --all-files
	-pre-commit run dprint --all-files
	-pre-commit run nixfmt --all-files

# The fast checks: the pre-commit stage on every file.
lint:
	pre-commit run --all-files

# The strict type check, through its hook.
typecheck:
	pre-commit run mypy --all-files

# The test suite.
test:
	uv run --frozen pytest

# Every check, once: the manual stage is the union of the pre-commit and the
# pre-push hooks. A green check is a green push.
check:
	pre-commit run --all-files --hook-stage manual

# Start the dashboard.
run *args:
	uv run --frozen vitals {{args}}
