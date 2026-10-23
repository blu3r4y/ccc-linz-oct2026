# Level 6 research log

Every approach tried for level 6, with what it bought and where its code lives. `SESSION.md` has the operational handoff (state, infrastructure, rules). On the remote boxes, each folder's own `README.md` (if present) has exact run commands.

Locations:
- `<SP>` = `C:\Users\mario\AppData\Local\Temp\claude\C--data-Dropbox-git-ccc-linz-oct2026\4eb86937-4366-4a15-b2ec-7ea93c8b2bfd\scratchpad`, local copies of the prototypes.
- `ccc1`/`ccc2` = the EC2 boxes (persisted). Each agent's folder is `~/scratch/l6_<name>`.

## The problem in one paragraph

- Hexagon of radius r; 6 border emitters in 3 parallel families (1/4 →←, 2/5 ↘↖, 3/6 ↙↗).
- Emitter e sits at an offset −(r−1)..r−1 (one full chord each). Per tick each emitter does one of F/B (move ±1), T (toggle) or -.
- Active beams fire every tick: a cell hit exactly 2× becomes M, 3+× becomes O; matter persists.
- A submission happens when all pattern cells are M and no halo cell (an in-board O next to the pattern) is M. It clears the pattern cells; at most 1 per tick.
- Program score = number of lines (ticks) to reach ≥ k submissions. Only medium, large and enormous are scored.

## Structural facts (all verified)

- After each submission the zone (pattern + halo) is all O, so each copy depends only on the emitter state it starts from. Cells outside the zone are don't-care.
- Opposite emitters at negated offsets share a chord; both on puts the whole chord at 2 hits.
- **Line space:** hits(c) = u_X[x] + u_Y[y] + u_Z[z] in cube coordinates, with each family contributing ≤ 2.
  - Point mode: ≤ 12 crossings per tick, triple points destroy.
  - Chord mode: a doubled family fills a whole chord, punctured by the other lines.
- **Validity is last-writer-wins:** each pattern cell's last touch has exactly 2 hits; each halo cell's last touch has 3+ (or it is never touched).
  - Pieces compose in sequence (reverse peeling is monotone), not in parallel, because the cross-family terms are global.
- Lower bound per item: Tfirst* + (k−1)·Pmin*, each proven by CP-SAT infeasibility at T−1 (practical for r ≤ 5).
- The judge (sandbox JS) was ported to Python at `<SP>\review6\judge.py`. It matches `valid6` on 553 real programs and 3000 fuzz programs.

## Score history (scored total = medium + large + enormous)

29042 (repo baseline, incl. small)
→ 28624 (frames)
→ 27029 (portfolio cycles)
→ 24386 (accumulation)
→ 24093 (relaxed cycles)
→ 21450 (lookahead greedy)
→ 17931 (numpy beam W=100)
→ 17690 (CP-SAT medium)
→ 16874 (exact chain on large)
→ 15621 (Rust beam on large)
→ … → **15250** (wide beams, CP-SAT LNS, chain).

The leader was at 14725 when the contest was closing.

## Approaches

| # | approach | code | outcome | lesson |
|---|---|---|---|---|
| 1 | Driver-pair BFS + greedy helpers (`baseline6`) | repo `ccc/contest.py` | baseline, 29042 | always valid, but 1 cell per tick |
| 2 | Single-tick frames / two-tick cycles | `<SP>\l6_frames` | small patterns only | 6 full-chord beams make ≤ 15 points |
| 3 | Repeat cycles portfolio (`frame6`/`pair6`/`triple6`/`cover6`/`toggle6`) | repo @316f8cf | medium −2000 | each repeat is the same problem |
| 4 | Relaxed cycles, sequence planner, replay (integrator) | `<SP>\l6_port\wip_final\` (also on ccc2) | small gains, superseded | slow; dropped from the repo |
| 5 | Movement scheduling, exact transition bounds | `<SP>\l6_sched` | informed 3/4 | movement is nearly free; LB = max(ringdist + toggle) |
| 6 | **Accumulation**: 4^6 per-tick greedy, line fills, SA cycles, `la.py`/`la3.py` lookahead | `ccc2:~/scratch/l6_accum` | big early jumps | exhaustive per-tick evaluation plus lookahead |
| 7 | **numpy beam over 4^6** (W 100–1600, beta/mu/nu/gamma, lookahead rescoring) | `ccc2:~/scratch/l6_big` | large −1600, enormous −1500 | compute-bound: wider is better |
| 8 | **Rust beam engine** (u64 bitsets, ~100M combos/s/thread, W up to 12000, seeds) | `ccc1:~/scratch/l6_rust` (local copy `<SP>\l6_rust`) | best on large/enormous | **the engine for future compute** |
| 9 | **Exact CP-SAT** (periodic/full/hinted improve) | `ccc2:~/scratch/l6_research` (`cpsat6.py`, `improve.py`) | medium proven optimal on 159/210 | tractable for r ≤ 5; can't construct for large from scratch |
| 10 | **Exact chain mode** (shortest rebuild per copy from the current emitter state) | `ccc1:~/scratch/l6_ilp` (`periodic.py MODE=chain`, results in `results/*.jsonl`) | large −160 and more | a strong polisher for large |
| 11 | **CP-SAT windowed LNS** (16/24-tick windows, hinted) | `ccc1:~/scratch/l6_cpsat` | steady 2–11 lines per item | 120 s per item pays off; 30 s does not |
| 12 | Collinear line sweeps + 4 erasers | `ccc2:~/scratch/l6_lines` | −40 | single family, ≤ 4 halo cuts per line: fails on holey shapes |
| 13 | Local search / SA shrink | `ccc2:~/scratch/l6_search` | −12% on weak programs, <1% on the best | annealing plateaus; structure matters more |
| 14 | A*/IDA*/beam-A* in C | `ccc1:~/scratch/l6_astar` | 0 net wins | exact only for builds of ≤ 3 ticks; branching 1000–2000 |
| 15 | Sculpture (sweep with cutters → carve → detail), Rust | `ccc1:~/scratch/l6_sculpt/rs` | 0 net wins | the sweep works; carving scattered halo holes needs a routing planner |
| 16 | Bottleneck diagnostics | `<SP>\l6_diag` | see below | compute-bound; thin/holey patterns dominate |
| 17 | Theory: line space / decomposition | `<SP>\l6_theory` | see below | ~90% of cells are built in point mode; chord mode unused |
| 18 | Tooling study (CP-SAT/MaxSAT/MILP, Rust speed) | `ccc2:~/scratch/l6_research` | Rust is 37× (sim) and 150–190× (combos) faster than Python | CP-SAT for medium plus polishing; Rust for search |

## Diagnostics (on the best set at about 15:15–15:40 UTC)

- Ticks: about 83–91% build, about 4% move-only after the beam, 0% idle. Rebuild ratio about 1.00.
- Density: about 4.1–4.2 pattern cells per productive tick (cap 12 in point mode). 50–55% of build ticks make only 1–3 cells.
- **Shape classes over large and enormous:**

  | class | items | lines | cells per line |
  |---|---|---|---|
  | thin/curvy | 136 | 3590 | 2.74 |
  | holey thin | 98 | 3878 | 3.45 |
  | holey mixed | 24 | 1338 | 4.1 |
  | mixed | 34 | 809 | 4.5 |
  | blob | 36 | 1355 | 4.9 |

- Beam width scaling on a 15-item sample: W 25/100/400/1600 gave 500/482/439/423 lines; on 10 items W=6400 gave 153 vs 159 at W=1600. Per item the results are noisy, so take the min over variants.
- Worst items at the time: L143, E64, E122, L64, E114, L141, E103, E113, E12, E51, L172, E117, E57, L184, L103, E125, E132.

## Most promising next steps (for a new session)

1. **Hybrid chord-cover constructor** (theory agent, est. −1000 to −1700 on enormous):
   - pick cheap chords (≤ 4 halo cells) from all 3 families to cover P, plus point stamps for the rest;
   - order them as runs of adjacent chords per family, with a small beam planning the puncture cursors;
   - feasibility check by reverse peeling.
2. **Rust beam with a chord-mode bonus/seed:** reward ticks where an opposite pair fills a chord with its halo punctured. A cheap change.
3. **Carve-routing planner** to finish the sculpture approach: route triples of cross-family beams to the scattered leftover halo cells.
4. Keep CP-SAT chain mode and windowed LNS as polishers of every new best program.
5. Wider and longer Rust beams on the thin/holey items (still compute-bound).

## Tools

- `merge6.py`, `peritem6.py`, `harvest6.sh` and `remote.sh` live in `tools/l6/` (copied into the repo) and in `<SP>`. See `SESSION.md` for usage.
