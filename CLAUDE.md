# CCC Linz Oct 2026

Python solutions for the Classic Cloudflight Coding Contest (codingcontest.org). Time-boxed contest: speed over polish.

## Contest format

- Levels 1..N unlock one after another. Each level has a spec PDF plus inputs `levelN_0.in` (example, comes with its `.out`) and `levelN_1.in`, `levelN_2.in`, ... (the real ones, uploaded for scoring).
- The user drops everything into `data/`: `data/Level N.pdf`, `data/levelN_M.in`, `data/levelN_0.out`. Read the PDF for the spec.
- Later levels usually extend earlier ones, so evolve the code in place rather than starting over.
- The contest also asks for the source code as a zip: `git archive --format zip -o code.zip HEAD`.

## Code layout

- `ccc/__main__.py`: `load(lines) -> dict` parses an input file. Runs the **highest level found in `data/`** across all its quests and writes `data/levelN_M.out` (this overwrites the example `levelN_0.out`, so check it with `git diff data/` before trusting it).
- `ccc/contest.py`: `solve(data) -> str` is the solution.
- `ccc/utils.py`: infers the level and quests from the filenames.
- Tests: `ccc/*_test.py` (pytest, configured in VS Code).
- `ccc/scratchpad.ipynb`: notebook for exploring.

## Commands

```sh
uv sync                      # Python 3.14, deps: numpy scipy networkx funcy loguru matplotlib
uv run python -m ccc         # solve the current level
uv run pytest ccc            # tests
uv run ruff format && uv run ruff check --select I --fix
```

## Git workflow

- One commit per level ("Solve level N"), plus a tag `levelN` (the README links to `/../levelN/ccc/contest.py`). Also tick the level off in the README.
- The user commits themselves. Don't commit unless asked.
- Remote: `git@github.com:blu3r4y/ccc-linz-oct2026.git`. Pushing needs the user's ssh-agent, so ask them to run `! git push --follow-tags`.
- Reference from the last contest: `../ccc-linz-nov2025`.
