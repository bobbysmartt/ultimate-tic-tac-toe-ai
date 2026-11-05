import math
import time
import unittest

from ultimate_ttt.__main__ import play_game
from ultimate_ttt.ai import WIN_SCORE, MinimaxAI, RandomAI, evaluate
from ultimate_ttt.board import O, X, UltimateBoard

from tests.test_board import position


def plain_minimax(board, depth):
    """Reference minimax without pruning, used to check that alpha-beta gives the same value."""
    if board.winner is not None:
        return {X: WIN_SCORE + depth, O: -WIN_SCORE - depth}.get(board.winner, 0)
    if depth == 0:
        return evaluate(board)
    values = []
    for move in board.legal_moves():
        board.play(move)
        values.append(plain_minimax(board, depth - 1))
        board.undo()
    return max(values) if board.player == X else min(values)


def random_position(seed, n_moves):
    board, player = UltimateBoard(), RandomAI(seed=seed)
    for _ in range(n_moves):
        if board.is_over():
            break
        board.play(player.choose_move(board))
    return board


class MinimaxTest(unittest.TestCase):
    def test_alpha_beta_returns_the_same_value_as_plain_minimax(self):
        ai = MinimaxAI(time_limit=None, max_depth=3)
        for seed in range(8):
            board = random_position(seed, n_moves=10 + seed)
            if board.is_over():
                continue
            self.assertEqual(ai._minimax(board, 3, -math.inf, math.inf), plain_minimax(board, 3))

    def test_takes_a_winning_move(self):
        board = position(x_cells=[(2, 0), (2, 1)], o_cells=[(2, 4)], status={0: X, 1: X}, next_board=2)
        self.assertEqual(MinimaxAI(time_limit=None, max_depth=2).choose_move(board), (2, 2))

    def test_never_lets_the_opponent_win_next_move(self):
        # O owns boards 0 and 1 and threatens to take board 2 (and the game) with cell 2.
        # X must play in board 4: cell 2 sends O to board 2, cells 0 and 1 give O a free choice.
        board = position(o_cells=[(2, 0), (2, 1)], status={0: O, 1: O}, next_board=4, player=X)
        board_after, cell = MinimaxAI(time_limit=None, max_depth=2).choose_move(board)
        self.assertEqual(board_after, 4)
        self.assertNotIn(cell, (0, 1, 2))

    def test_respects_the_time_limit(self):
        ai = MinimaxAI(time_limit=0.2)
        start = time.monotonic()
        result = ai.search(UltimateBoard())
        self.assertLess(time.monotonic() - start, 0.6)
        self.assertGreaterEqual(result.depth, 2)

    def test_beats_a_random_player(self):
        wins = 0
        for g in range(4):
            ai, opponent = MinimaxAI(time_limit=0.05), RandomAI(seed=g)
            ai_side = X if g % 2 == 0 else O
            players = (ai, opponent) if ai_side == X else (opponent, ai)
            wins += play_game(*players, verbose=False) == ai_side
        self.assertGreaterEqual(wins, 3)


if __name__ == "__main__":
    unittest.main()
