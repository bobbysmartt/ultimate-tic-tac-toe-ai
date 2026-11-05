"""Ultimate Tic Tac Toe rules.

The game is a 3x3 grid of small 3x3 boards. A move is a pair (board, cell),
both indexed 0-8 in reading order. Playing in cell c sends the opponent to
small board c. If that board is already won or full, the opponent may play
in any open board. Winning three small boards in a row wins the game.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

X = 1
O = -1
EMPTY = 0

OPEN = 0
DRAW = 2

LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)
LINES_THROUGH = tuple(tuple(line for line in LINES if i in line) for i in range(9))

Move = Tuple[int, int]


class UltimateBoard:
    def __init__(self) -> None:
        self.cells: List[int] = [EMPTY] * 81
        self.status: List[int] = [OPEN] * 9
        self.player: int = X
        self.next_board: Optional[int] = None
        self.winner: Optional[int] = None
        self._history: List[Tuple[Move, Optional[int], int, Optional[int]]] = []

    def cell(self, board: int, cell: int) -> int:
        return self.cells[board * 9 + cell]

    def is_over(self) -> bool:
        return self.winner is not None

    def legal_moves(self) -> List[Move]:
        if self.winner is not None:
            return []
        if self.next_board is not None:
            boards = [self.next_board]
        else:
            boards = [b for b in range(9) if self.status[b] == OPEN]
        return [(b, c) for b in boards for c in range(9) if self.cells[b * 9 + c] == EMPTY]

    def play(self, move: Move) -> None:
        b, c = move
        if self.winner is not None:
            raise ValueError("the game is over")
        if self.next_board is not None and b != self.next_board:
            raise ValueError(f"must play in board {self.next_board}, not {b}")
        if self.status[b] != OPEN or self.cells[b * 9 + c] != EMPTY:
            raise ValueError(f"illegal move {move}")

        self._history.append((move, self.next_board, self.status[b], self.winner))
        self.cells[b * 9 + c] = self.player

        if self._wins_small_board(b, c, self.player):
            self.status[b] = self.player
            if any(all(self.status[i] == self.player for i in line) for line in LINES_THROUGH[b]):
                self.winner = self.player
        elif EMPTY not in self.cells[b * 9:b * 9 + 9]:
            self.status[b] = DRAW

        if self.winner is None and OPEN not in self.status:
            self.winner = DRAW

        self.next_board = c if self.status[c] == OPEN else None
        self.player = -self.player

    def undo(self) -> None:
        (b, c), next_board, status_b, winner = self._history.pop()
        self.cells[b * 9 + c] = EMPTY
        self.status[b] = status_b
        self.next_board = next_board
        self.winner = winner
        self.player = -self.player

    def _wins_small_board(self, b: int, c: int, player: int) -> bool:
        base = b * 9
        return any(all(self.cells[base + i] == player for i in line) for line in LINES_THROUGH[c])

    def render(self) -> str:
        symbols = {X: "X", O: "O", EMPTY: "."}
        rows = []
        for r in range(9):
            if r in (3, 6):
                rows.append("  " + "+".join(["-------"] * 3))
            parts = []
            for block in range(3):
                b = (r // 3) * 3 + block
                row_cells = [symbols[self.cell(b, (r % 3) * 3 + k)] for k in range(3)]
                parts.append(" " + " ".join(row_cells) + " ")
            rows.append(f"{r + 1} " + "|".join(parts))
        header = "   " + "   ".join(" ".join(str(col) for col in range(start, start + 3)) for start in (1, 4, 7))
        return header + "\n" + "\n".join(rows)


def to_global(move: Move) -> Tuple[int, int]:
    """Convert (board, cell) to 0-based (row, column) on the 9x9 grid."""
    b, c = move
    return (b // 3) * 3 + c // 3, (b % 3) * 3 + c % 3


def from_global(row: int, col: int) -> Move:
    """Convert 0-based (row, column) on the 9x9 grid to (board, cell)."""
    return (row // 3) * 3 + col // 3, (row % 3) * 3 + col % 3
