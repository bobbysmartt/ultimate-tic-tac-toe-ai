# Ultimate Tic Tac Toe AI

A game-playing AI for Ultimate Tic Tac Toe, built on minimax search with alpha-beta pruning, a hand-written evaluation heuristic and iterative deepening under a per-move time limit. Pure Python, no dependencies.

## The game

The board is a 3x3 grid of small tic-tac-toe boards.

- Where you play decides where your opponent plays next: a move in the top-right cell of a small board sends the opponent to the top-right small board.
- Three in a row on a small board wins that board. If you are sent to a board that is already won or full, you may play in any open board.
- Winning three small boards in a row wins the game.

The rule that every move picks the opponent's next board makes greedy play fail: winning a small board is often a mistake if it hands the opponent a free move.

## How the AI works

**Search.** The game tree is far too large to explore fully (81 first moves, then up to 9 to 81 per turn), so the AI runs minimax to a fixed depth and scores the leaves with a heuristic. Alpha-beta pruning skips branches that cannot change the decision, and move ordering (moves that win or block a small board first, center and corners next, moves that give the opponent a free choice last) makes it prune much more.

**Time limit.** Iterative deepening searches depth 1, then 2, then 3, and so on, until the time budget runs out. The AI plays the best move of the deepest search that finished, and starts each new depth with the previous best move, which tightens the pruning. With a 1-second budget it reaches depth 5 to 6 (about 15,000 to 20,000 positions per second in CPython on a laptop).

**Heuristic** (`evaluate` in [`ultimate_ttt/ai.py`](ultimate_ttt/ai.py)), scored from X's point of view:

- small boards won, weighted by their position on the big board (center > corners > edges, i.e. by how many winning lines go through them);
- big-board lines still open to only one player: one won board, or two won boards (a strong threat);
- the same line count inside each open small board, weighted by that board's position;
- a bonus for the side to move when it may play in any board.

Wins are scored with the remaining depth added, so the AI prefers the fastest win and the slowest loss.

## Usage

Requires Python 3.9 or newer.

```bash
python -m ultimate_ttt                          # you play X against the AI
python -m ultimate_ttt --x ai --o human         # the AI starts
python -m ultimate_ttt --x ai --o ai --time 0.5 # AI against itself
python -m ultimate_ttt --bench 20 --time 0.1    # AI against a random player
```

Enter moves as `row column` on the 9x9 grid, for example `5 5` for the very center.

## Results

- Against a random player, with 0.1 s per move: 20 wins out of 20 games, playing both sides.
- Alpha-beta is checked against a plain minimax in the tests: both return exactly the same value, alpha-beta just visits fewer positions.

## Tests

```bash
python -m unittest -v
```

The tests cover the rules (send rule, free choice, small-board and game wins, draws), `undo` restoring the exact state, alpha-beta correctness, the time limit, and simple tactics (taking a winning move, never sending the opponent to a board where it wins the game).

## Code layout

```
ultimate_ttt/board.py     game rules, play/undo, rendering
ultimate_ttt/ai.py        heuristic, move ordering, minimax with alpha-beta, iterative deepening
ultimate_ttt/__main__.py  command-line interface and benchmark
tests/                    unit tests
```

## Context

Originally built for a class tournament in which students' AIs played each other under a per-move time limit. This repository is a clean rewrite of that project.
