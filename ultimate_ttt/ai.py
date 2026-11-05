"""Game-playing AI: minimax with alpha-beta pruning under a time limit.

The full game tree is far too large to search, so the search stops at a
fixed depth and scores the position with a hand-written heuristic.
Iterative deepening (depth 1, 2, 3, ...) makes the AI respect a per-move
time budget: it always returns the best move of the deepest search that
finished in time.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import List, Optional

from .board import DRAW, EMPTY, LINES, LINES_THROUGH, O, OPEN, X, Move, UltimateBoard

WIN_SCORE = 1_000_000

# Heuristic weights, all scored from X's point of view.
BOARD_WEIGHT = (3, 2, 3, 2, 4, 2, 3, 2, 3)  # center board > corners > edges (number of meta lines through it)
WON_BOARD = 60
META_TWO = 400  # two won boards in a meta line whose third board is still open
META_ONE = 40
SMALL_TWO = 12  # two marks in a small-board line whose third cell is empty
SMALL_ONE = 2
FREE_CHOICE = 25  # bonus for the side to move when it may play in any board

CELL_PRIORITY = (2, 1, 2, 1, 3, 1, 2, 1, 2)


class SearchTimeout(Exception):
    pass


@dataclass
class SearchResult:
    move: Move
    score: float
    depth: int
    nodes: int


def _line_value(a: int, b: int, c: int, one: int, two: int) -> int:
    """Score one line: positive when only X can still complete it, negative for O."""
    if DRAW in (a, b, c):
        return 0
    xs = (a == X) + (b == X) + (c == X)
    os = (a == O) + (b == O) + (c == O)
    if xs and os:
        return 0
    if xs == 2:
        return two
    if xs == 1:
        return one
    if os == 2:
        return -two
    if os == 1:
        return -one
    return 0


def evaluate(board: UltimateBoard) -> float:
    """Static evaluation of a non-terminal position, from X's point of view."""
    if board.winner is not None:
        return {X: WIN_SCORE, O: -WIN_SCORE}.get(board.winner, 0)

    status, cells = board.status, board.cells
    score = 0

    for b in range(9):
        if status[b] == X:
            score += WON_BOARD * BOARD_WEIGHT[b]
        elif status[b] == O:
            score -= WON_BOARD * BOARD_WEIGHT[b]

    for i, j, k in LINES:
        score += _line_value(status[i], status[j], status[k], META_ONE, META_TWO)

    for b in range(9):
        if status[b] != OPEN:
            continue
        base = b * 9
        weight = BOARD_WEIGHT[b]
        for i, j, k in LINES:
            score += weight * _line_value(cells[base + i], cells[base + j], cells[base + k], SMALL_ONE, SMALL_TWO)

    if board.next_board is None:
        score += FREE_CHOICE * board.player

    return score


def _completes_line(board: UltimateBoard, b: int, c: int, player: int) -> bool:
    base = b * 9
    return any(
        all(board.cells[base + i] == player for i in line if i != c)
        for line in LINES_THROUGH[c]
    )


def order_moves(board: UltimateBoard, moves: List[Move]) -> List[Move]:
    """Sort moves so the most promising come first, which makes alpha-beta prune more."""
    player = board.player

    def priority(move: Move) -> int:
        b, c = move
        wins_board = _completes_line(board, b, c, player)
        p = CELL_PRIORITY[c]
        if wins_board:
            p += 100
        if _completes_line(board, b, c, -player):
            p += 50
        sends_to_closed = board.status[c] != OPEN or (c == b and wins_board)
        if sends_to_closed:
            p -= 20
        return -p

    return sorted(moves, key=priority)


class MinimaxAI:
    def __init__(self, time_limit: Optional[float] = 1.0, max_depth: Optional[int] = None) -> None:
        if time_limit is None and max_depth is None:
            raise ValueError("set a time limit, a maximum depth, or both")
        self.time_limit = time_limit
        self.max_depth = max_depth
        self.nodes = 0
        self._deadline = math.inf

    def choose_move(self, board: UltimateBoard) -> Move:
        return self.search(board).move

    def search(self, board: UltimateBoard) -> SearchResult:
        moves = order_moves(board, board.legal_moves())
        if not moves:
            raise ValueError("no legal move: the game is over")
        self.nodes = 0
        self._deadline = math.inf if self.time_limit is None else time.monotonic() + self.time_limit
        best = SearchResult(moves[0], evaluate(board), 0, 0)
        empty_cells = board.cells.count(EMPTY)

        depth = 1
        while self.max_depth is None or depth <= self.max_depth:
            try:
                move, score = self._search_root(board, moves, depth)
            except SearchTimeout:
                break
            best = SearchResult(move, score, depth, self.nodes)
            if abs(score) >= WIN_SCORE or depth >= empty_cells:
                break
            moves.remove(move)
            moves.insert(0, move)
            depth += 1
        return best

    def _search_root(self, board: UltimateBoard, moves: List[Move], depth: int):
        maximizing = board.player == X
        alpha, beta = -math.inf, math.inf
        best_move, best_score = moves[0], (-math.inf if maximizing else math.inf)
        for move in moves:
            board.play(move)
            try:
                score = self._minimax(board, depth - 1, alpha, beta)
            finally:
                board.undo()
            if maximizing and score > best_score:
                best_move, best_score = move, score
                alpha = max(alpha, score)
            elif not maximizing and score < best_score:
                best_move, best_score = move, score
                beta = min(beta, score)
        return best_move, best_score

    def _minimax(self, board: UltimateBoard, depth: int, alpha: float, beta: float) -> float:
        self.nodes += 1
        if self.nodes % 1024 == 0 and time.monotonic() > self._deadline:
            raise SearchTimeout

        if board.winner is not None:
            # Adding the remaining depth makes the AI prefer faster wins and slower losses.
            if board.winner == X:
                return WIN_SCORE + depth
            if board.winner == O:
                return -WIN_SCORE - depth
            return 0
        if depth == 0:
            return evaluate(board)

        if board.player == X:
            value = -math.inf
            for move in order_moves(board, board.legal_moves()):
                board.play(move)
                try:
                    value = max(value, self._minimax(board, depth - 1, alpha, beta))
                finally:
                    board.undo()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value

        value = math.inf
        for move in order_moves(board, board.legal_moves()):
            board.play(move)
            try:
                value = min(value, self._minimax(board, depth - 1, alpha, beta))
            finally:
                board.undo()
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


class RandomAI:
    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def choose_move(self, board: UltimateBoard) -> Move:
        return self._rng.choice(board.legal_moves())
