# Contributing

Thanks for your interest in pluginkit. The library is intentionally small and
dependency-free; changes should keep it that way.

## Setup

```bash
make install        # uv sync (library + examples + docs tooling)
```

Requires [uv](https://docs.astral.sh/uv/). pluginkit targets **Python 3.11+**.

## Develop

```bash
make test           # pytest
make lint           # ruff format + check, mypy, pyright (all must pass)
make coverage       # tests with coverage
make docs-serve     # preview the docs at http://127.0.0.1:8000
```

CI runs `make lint` and tests across Python 3.11, 3.12, and 3.13. Please add or
update tests for any behaviour change, and keep the library free of runtime
dependencies.

## Commits and PRs

- **[Conventional Commits](https://www.conventionalcommits.org/)** for every commit
  and PR title, e.g. `feat(manager): add call_extra`, `fix(aio): ...`, `docs: ...`.
- **Signed commits are required** - the repo enforces verified signatures on all
  branches. Configure signing once
  ([GitHub docs](https://docs.github.com/authentication/managing-commit-signature-verification)),
  e.g. `git config --global commit.gpgsign true`.
- Branch names follow `<type>/<short-description>` (e.g. `feat/historic-replay`).
- Open the PR against `main`; the branch is deleted automatically on merge.

## Releases

Maintainers cut releases by bumping `version` in `pyproject.toml`, updating
`CHANGELOG.md`, and pushing a matching `vX.Y.Z` tag - the release workflow builds
and publishes to PyPI via trusted publishing.
