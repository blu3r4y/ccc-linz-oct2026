# CCC Linz Oct 2026

Python solutions for the Classic Cloudflight Coding Contest (codingcontest.org). Time-boxed contest: speed over polish.

## Contest format

- Levels 1..N unlock one after another. Each level has a spec PDF, an example input with its expected output, and the real inputs, which get uploaded for scoring.
- The user drops everything into `data/`. **This contest's naming** (unlike the `levelN_M.in` of past contests): `data/level-N.pdf`, `data/in_level-N_M-<name>.txt` (`0-example`, `1-small`, `2-large`, ...), and `data/out_level-N_0-example.txt`. Write outputs next to the inputs as `out_level-N_M-<name>.txt`. Read the PDF for the spec.
- Later levels usually extend earlier ones, so evolve the code in place rather than starting over.
- The contest also asks for the source code as a zip: `git archive --format zip -o code.zip HEAD`.

## Code layout

- `ccc/__main__.py`: `load(lines) -> dict` parses an input file into `{"items": [...]}`: a count line, then N items with blank lines between them. The shape of each item's header line picks the format: `r rows cols` plus the rows gives a `Board` (L2, L3), or a `Task` `(r, pattern, ticks)` if a lone tick count follows the rows (L5). A lone `r` gives a `Program` `(r, ticks)` (L4). `r rows cols count` plus the rows gives an `Order` `(r, pattern, count)` (L6). `read_ticks` parses a tick count plus its ticks. A new input format means a new branch there. The user wants the main loop **left as is**. That loop still expects `levelN_M.in` (and so does `ccc/utils.py`), so `python -m ccc` finds nothing for this contest's files. Use `ccc.run` instead.
- `ccc/contest.py`: `solve(data, level=None) -> str` is the solution. It applies the level's rule to each item. A rule returns either a `Board`, in which case the results are rendered and joined with `"\n\n"`, a program (a `list` of ticks), joined the same way with one tick per line, or a plain answer such as an `int`, in which case they're joined one per line. Levels in `PARALLEL` spread their items over processes (`ProcessPoolExecutor`), so a script that calls `solve` for them needs an `if __name__ == "__main__":` guard on Windows. There's no trailing newline. `level=None` means the latest level.
  - **New level = new rule function (`fireN`, `runN`, ...) + one entry in `RULES = {level: rule}`** at the bottom of the file. Keep old rules as they are, so old levels stay solvable and tested. Reuse the building blocks (`ray`, `beam_hits`, ...), and split one out when a new level needs part of an old rule.
  - `Board = dict[(row, col), char]`, keyed by ASCII position with the `-` gaps left out ("doubled-width" coordinates; chosen over axial, numpy, or the raw grid).
  - `parse` / `render` convert to and from the ASCII rows. `ray(board, start, digit)` yields the cells a beam crosses (through `O`/`M`) until the border. `hits(board, emitters)` counts the beams over each cell (`beam_hits` does it for the emitters drawn on the board), `create_or_destroy` applies the 2 / 3+ rule, and `ring(r)` lists the border cells clockwise from the west corner. `iter_ticks(board, r, ticks)` runs a moving-emitter program on any board and yields the board (changed in place) after each tick, so a rule can inspect or edit it between ticks (L5). `run_ticks` runs all the ticks (`run4` calls it on an empty hexagon). `neighbours(cell)` gives the 6 adjacent cells. `hexagon(r)` draws an empty board (L1).
  - `DIRS`: emitter digit -> step, `1=(0,2)` →, `2=(1,1)` ↘, `3=(1,-1)` ↙, `4=(0,-2)` ←, `5=(-1,-1)` ↖, `6=(-1,1)` ↗. Clockwise, so turning is index arithmetic mod 6.
  - Only `parse`, `render`, `DIRS`, `ray`, `neighbours`, `hexagon` and `ring` touch raw coordinates. Everything else treats cells as opaque keys (`cell in board`, a `Counter`), so a switch to axial coordinates only changes those.
- `ccc/run.py`: `uv run python -m ccc.run [N] [filter]` (default: the latest level in `RULES`; `filter` keeps only inputs whose name contains it, plus the example). It checks the example against `out_level-N_0-example.txt` (and exits if it doesn't match), then writes `out_level-N_*.txt` for the real inputs. Levels in `CHECKS = {level: validator(item, answer)}` (optimization levels, many valid answers) are validated per item instead of diffed: it prints `valid, N lines` (plus the reference's line count for the example), never overwrites the example output, and exits on any invalid answer.
- `ccc/utils.py`: infers the level and quests from `levelN_M.in` filenames (doesn't match this contest's naming).
- Tests: `ccc/contest_test.py`. Once a level is in `RULES` (and not in `CHECKS`), `test_outputs` checks every `out_level-N_*.txt` that exists (the example and the confirmed uploads) against `solve(load(in), N)`, so old levels can't silently regress. `test_load_boards` round-trips every input board (add a level to `BOARD_LEVELS` if its items are boards). Add a small hand-traced rule test per level on `hexagon(2)` (the `small()` helper).
- `ccc/scratchpad.ipynb`: notebook for exploring.

## Levels so far

- L1: draw a hexagon board of radius r.
- L2: one emitter, its beam turns `O` into `M` until the border.
- L3: multiple emitters. A cell hit by 2 beams becomes `M`, 3+ hits destroy it, 0-1 hits leave it unchanged. The output may keep the emitter digits.
- L4: input is programs, not boards (`r`, tick count, ticks of 6 commands `F`/`B`/`T`/`-`). The six emitters start off on the corners (emitter d at `ring(r)[(d-1)*r]`) and move along the border; each tick, all commands apply at once, then the active emitters fire with the L3 rule. Emitters are kept off the board dict, because they can share a cell. Output is rendered without emitters.
- L5: each item is a pattern board plus an L4 program on an empty board. After each tick, if all the pattern's `M` cells are `M` and no other `M` touches them, the pattern is submitted: its cells go back to `O`, and the count goes up by 1. Output is one count per line. Programs with 0 ticks occur.
- L6 (optimization): each item is a pattern plus a required count. Output one program per item (no count line, blank line between programs) that submits the pattern exactly `count` times under the L5 rules. Score = total lines, lower is better. `valid6` checks `run5(...) == count`; `test_valid_outputs` checks every `out_level-6_*.txt`. `program6` is a greedy over interior-cell bitmasks (`chords`, `count_hits`): a driver pair of emitters on two axes BFS-walks (`drive`) to cross on the next unbuilt pattern cell, while the other 4 emitters try all <= 4^4 command combinations per tick (never 2 hits on the pattern's halo, never 3+ on a built cell). Best of 6 driver pairs. About 17-22 s per big file on 14 cores.

## Commands

```sh
uv sync                      # Python 3.14, deps: numpy scipy networkx funcy loguru matplotlib
uv run pytest ccc -q         # tests
uv run ruff format && uv run ruff check --select I --fix
```

Write the outputs for level N (it checks the example first). The optional filter keeps only inputs whose name contains it (the example always runs), and each file's timing is printed:

```sh
uv run python -m ccc.run [N] [filter]   # e.g. uv run python -m ccc.run 6 small
```

When trying a new solver, wrap it in `timeout` so a slow input can't hang the run: `timeout 300 uv run python -m ccc.run 6`.

Write or edit Python files with the Write/Edit tools, not Python heredocs in Bash: on this Windows machine, `\n` escapes in a heredoc came out as literal newlines with CRLF.

## Per-level loop

1. New level files land in `data/`. Start a **Plan** sub-agent to read the PDF and data, verify its reading against the example with read-only scripts, and plan the code changes. It can't edit files, so it never implements.
2. Implement (yourself, or a **general-purpose** sub-agent), then run `python -m ccc.run N`, which must print "example OK".
3. The user uploads the outputs and confirms. Then, often through a sub-agent: review, test, make it readable, update `CLAUDE.md` and the README, commit, and tag.
4. The user likes running these in parallel: plan level N+1 while level N gets reviewed and committed. Never let two agents edit the same file at the same time. Give each agent an explicit list of files to stage.

## Performance notes (for upcoming levels)

- A ray's cells depend only on geometry (`r`, start, direction), not on matter, because beams pass through `O` and `M` and stop only at the border. So rays can be cached per radius with `lru_cache`.
- If a level asks for the program or placement that **produces** a target board, don't brute-force it: with 6 emitters on 6r border cells, that's on the order of (6r)^6 * 2^6 combinations.
  - Each cell's result depends only on how many active rays cover it, so model it as constraints. Precompute every ray's cells, then search with pruning (or `scipy.optimize.milp`). Use `int` bitsets or numpy masks if the checks get hot.
- Items are independent, so a slow level can be spread across processes in `run.py` with `ProcessPoolExecutor.map`.
- If large files make the solver slow, mark them `slow` in `test_outputs` so the default test run stays fast.

## Git workflow

- One commit per level ("Solve level N"), plus a tag `levelN`. Commit the level's `data/` files too (PDF, inputs, outputs). Tick the level off in the README's `## Challenges` list: `- :heavy_check_mark: **[Level N](data/level-N.pdf)** - [Solution](/../levelN/ccc/contest.py)`.
- The user uploads the outputs and confirms they're correct. Only then commit the level, staging only that level's `data/` files, never the next level's.
- The user commits themselves. Don't commit unless asked. "Commit it" in a level request covers that level only.
- `DOCS.html` at the repo root is a short guide for human developers. Keep it in sync when the architecture changes.
- Remote: `git@github.com:blu3r4y/ccc-linz-oct2026.git`. Pushing needs the user's ssh-agent, so ask them to run `! git push --follow-tags`.
- Reference from the last contest: `../ccc-linz-nov2025`.
