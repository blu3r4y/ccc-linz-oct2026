# 43rd Classic Cloudflight Coding Contest

My solutions for the [43rd Classic Cloudflight Coding Contest](https://codingcontest.org/) in October 2026, written in Python.

:goat: :goat: :goat:

## Requirements

### Python >= 3.14

Package requirements are specified in the [pyproject.toml](pyproject.toml) file.

```sh
uv sync
```

Lint and format before commits.

```sh
uv run ruff format
uv run ruff check --select I --fix
```

## Snippets

Run code as a module

```sh
uv run python -m ccc
```

Quickly archive the last commit

```sh
git archive --format zip -o code.zip HEAD
```
