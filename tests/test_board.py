import unittest

from ultimate_ttt.ai import RandomAI
from ultimate_ttt.board import DRAW, EMPTY, O, OPEN, X, UltimateBoard, from_global, to_global


def position(x_cells=(), o_cells=(), status=None, next_board=None, player=X):
    """Build a position directly. Cells are (board, cell) pairs."""
    board = UltimateBoard()
    for b, c in x_cells:
        board.cells[b * 9 + c] = X
    for b, c in o_cells:
        board.cells[b * 9 + c] = O
    for b, s in (status or {}).items():
        board.status[b] = s
    board.next_board = next_board
    board.player = player
    return board


class RulesTest(unittest.TestCase):
    def test_first_move_can_go_anywhere(self):
        self.assertEqual(len(UltimateBoard().legal_moves()), 81)

    def test_move_sends_opponent_to_matching_board(self):
        board = UltimateBoard()
        board.play((4, 0))
        moves = board.legal_moves()
        self.assertEqual(len(moves), 9)
        self.assertTrue(all(b == 0 for b, _ in moves))
        self.assertEqual(board.player, O)

    def test_three_in_a_row_wins_small_board(self):
        board = position(x_cells=[(0, 0), (0, 1)], next_board=0)
        board.play((0, 2))
        self.assertEqual(board.status[0], X)
        self.assertEqual(board.next_board, 2)
        self.assertIsNone(board.winner)

    def test_sent_to_closed_board_means_free_choice(self):
        board = position(status={5: O}, next_board=3)
        board.play((3, 5))
        self.assertIsNone(board.next_board)
        boards = {b for b, _ in board.legal_moves()}
        self.assertEqual(boards, set(range(9)) - {5})

    def test_full_small_board_without_line_is_a_draw(self):
        # X O X / X O O / O X . -> X fills the last cell without a line
        x_cells = [(3, 0), (3, 2), (3, 3), (3, 7)]
        o_cells = [(3, 1), (3, 4), (3, 5), (3, 6)]
        board = position(x_cells, o_cells, next_board=3)
        board.play((3, 8))
        self.assertEqual(board.status[3], DRAW)
        self.assertIsNone(board.winner)

    def test_three_small_boards_in_a_row_wins_the_game(self):
        board = position(x_cells=[(2, 0), (2, 1)], status={0: X, 1: X}, next_board=2)
        board.play((2, 2))
        self.assertEqual(board.winner, X)
        self.assertEqual(board.legal_moves(), [])

    def test_game_is_drawn_when_every_board_is_closed(self):
        status = {0: X, 1: O, 2: X, 3: X, 4: O, 5: O, 6: O, 7: X}
        board = position(x_cells=[(8, 0), (8, 1)], status=status, next_board=8)
        board.play((8, 2))
        self.assertEqual(board.status[8], X)
        self.assertEqual(board.winner, DRAW)

    def test_illegal_moves_are_rejected(self):
        board = UltimateBoard()
        board.play((4, 0))
        with self.assertRaises(ValueError):
            board.play((5, 0))
        with self.assertRaises(ValueError):
            board.play((4, 0))

    def test_undo_restores_the_exact_state(self):
        board = UltimateBoard()
        snapshots = []
        player = RandomAI(seed=3)
        while not board.is_over():
            snapshots.append((board.cells[:], board.status[:], board.player, board.next_board, board.winner))
            board.play(player.choose_move(board))
        while snapshots:
            board.undo()
            self.assertEqual(
                (board.cells, board.status, board.player, board.next_board, board.winner), snapshots.pop()
            )
        self.assertEqual(board.cells, [EMPTY] * 81)
        self.assertEqual(board.status, [OPEN] * 9)

    def test_random_games_always_finish(self):
        for seed in range(50):
            board, player = UltimateBoard(), RandomAI(seed=seed)
            while not board.is_over():
                board.play(player.choose_move(board))
            self.assertIn(board.winner, (X, O, DRAW))

    def test_global_coordinates_round_trip(self):
        for row in range(9):
            for col in range(9):
                self.assertEqual(to_global(from_global(row, col)), (row, col))


if __name__ == "__main__":
    unittest.main()
