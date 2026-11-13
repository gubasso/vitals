# vitals

A terminal dashboard of the machine's vital signs, written in Python on Textual.

## Self-containment

This repository is complete on its own. Its specs, its decision records, and this file carry every rule that a change must meet, so an agent works from the repository alone and needs no outside context. A rule that a change depends on lives here, in `docs/`, or in the configuration of a tool, and nowhere else.

## The environment

- Run every command in the devshell: in a shell that direnv activated, or as `direnv exec . <command>`. The commit hooks find their tools only there.
- The host supplies `nix`, `direnv`, `git`, `uv`, and the hook runner `prek`, as [host-requirements.toml](./host-requirements.toml) lists. The devshell holds the project tools: `just`, `dprint`, `nixfmt`, `rk`, `sdd`, and `exobrain`.
- uv owns the Python interpreter. `.python-version` names the exact patch, and `[tool.uv] required-version` in `pyproject.toml` names the uv that the project accepts. Reach a tool of the project through `uv run`.
- `just check` runs every check once: the union of the pre-commit and the pre-push hooks.

## The specs

Load the spec of a domain before changing it:

- `docs/specs/SPEC-typing.md`: the typing contract that every module meets.
- `docs/specs/SPEC-collectors.md`: the data sources, the samples, and the error kinds.
- `docs/specs/SPEC-dashboard.md`: the panels, the views, and the key bindings.
- `docs/specs/SPEC-cli.md`: the flags, the exit codes, the configuration, and the logging.

<!-- BEGIN release-kit -->

## Releases

- This repository runs the release-kit convention. `rk method invariants` states what must stay true. A release needs a commit typed `feat`, `fix`, or `perf`, or a breaking change, that changed a file the package ships. A dependency update that changes what ships is `fix(deps)`, and one for development only is `chore(deps-dev)` or `build(deps-dev)`. A security update is always `fix(deps)`, also where it changes only a shipped lock file. Its body names the advisory ID: `RUSTSEC-`, `GHSA-`, or `CVE-`.
- An agent here guides and never drives. It reads this convention and tells the operator which step comes next. It takes no git or forge action unless the operator's request named that action. The bounded actions include the following. Create, switch, or delete a branch. Mint a branch at the forge from an issue. Create or remove a worktree. Commit, push, or tag. Integrate a branch onto the trunk, locally or through a request. Open, update, or merge a pull request. A request to change code authorizes the file changes alone.
- The workflow terms live in `GLOSSARY.md` at this repository's root. The terms release-kit owns there are `implement-and-request`, `implement-and-merge`, and `full-implement`. A request that carries one of them names every action that term lists.
- The title of every commit that reaches the trunk MUST be a scoped Conventional Commit, because the version and the changelog come from it.
- The request's title becomes that commit's message, and its body carries the context and lands with it. The body names no internal planning artifact and carries no agent attribution. The landed rk-message hook, the forge's body check, and the observed body source hold that rule.
- Every commit follows the same scoped convention. The landed commit-msg hook requires a scope on every one, and the title check holds it to lowercase letters, digits, and `_ . / -`.
- The scope names the area you changed, and reads as `area/subarea` where that is clearer. Prefer a scope this repository already uses, which `git log --format=%s | sed -n 's/^[a-z]*(\([^)]*\)).*/\1/p' | sort -u` lists. Coin a new scope only where no existing one names the area.
- Never author a tag, and never hand-edit a generated artifact workflow.
- Run `rk status` before changing anything under `.github/workflows/` or `.gitlab-ci.yml`, or any file `.release-kit/manifest.json` names. Before reading a gap in `rk setup check` as a setup defect, run `rk setup status`. A credential this runtime cannot reach leaves a step unknown, which is an observation boundary and not drift. Never ask the operator to mount, expose, recreate, or rotate a secret only so an agent check can pass.
- The full method is `rk method --list`. The recovery paths are `rk method recovery`.

<!-- END release-kit -->

<!-- BEGIN spec-driven-docs docs -->
## Documentation

- Load the affected specs before editing governed content: `docs/specs/SPEC-<domain>.md`. <!-- markdownlint-disable-line MD013 -->
- Treat decision records as immutable rationale and load them only when asked why. <!-- markdownlint-disable-line MD013 -->
- Read the writing style before you author or edit prose: `sdd method writing-style`. <!-- markdownlint-disable-line MD013 -->
- Write and edit step-by-step guides to the adopted guides spec, `docs/specs/SPEC-guides.md`. <!-- markdownlint-disable-line MD013 -->
- Name a document by a slug drawn from its subject, never by a number. Where its directory holds documents with no kind prefix, give that directory a `README.md` saying what it holds and what each document covers. <!-- markdownlint-disable-line MD013 -->
- For a question about this method or about operating `sdd`, run `sdd docs` and read only the topic it names. <!-- markdownlint-disable-line MD013 -->
- Run `sdd verify` before handoff. <!-- markdownlint-disable-line MD013 -->
- Keep adopted specs, the tracking registry, and local integration instance-owned. <!-- markdownlint-disable-line MD013 -->
<!-- END spec-driven-docs docs -->
