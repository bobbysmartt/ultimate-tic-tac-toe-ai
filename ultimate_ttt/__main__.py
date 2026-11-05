"""Command-line interface.

    python -m ultimate_ttt                          # you (X) against the AI (O)
    python -m ultimate_ttt --x ai --o human         # the AI starts
    python -m ultimate_ttt --x ai --o ai --time 0.5
    python -m ultimate_ttt --bench 20 --time 0.2    # AI against a random player
"""

from __future__ import annotations

import argparse
import time

from .ai import MinimaxAI, RandomAI
from .board import DRAW, O, X, UltimateBoard, from_global, to_global

NAMES = {X: "X", O: "O"}


class HumanPlayer:
    def choose_move(self, board: UltimateBoard):
        legal = set(board.legal_moves())
        while True:
            raw = input(f"{NAMES[board.player]} to play, enter row and column (1-9), e.g. '5 5': ").split()
            if len(raw) == 2 and all(part.isdigit() for part in raw):
                row, col = int(raw[0]) - 1, int(raw[1]) - 1
                if 0 <= row < 9 and 0 <= col < 9 and from_global(row, col) in legal:
                    return from_global(row, col)
            print("Illegal move, try again.")


def make_player(kind: str, time_limit: float):
    if kind == "human":
        return HumanPlayer()
    if kind == "random":
        return RandomAI()
    return MinimaxAI(time_limit=time_limit)


def describe_target(board: UltimateBoard) -> str:
    if board.next_board is None:
        return "any open board"
    b = board.next_board
    return f"the board at block row {b // 3 + 1}, block column {b % 3 + 1}"


def play_game(x_player, o_player, verbose: bool = True) -> int:
    board = UltimateBoard()
    players = {X: x_player, O: o_player}
    while not board.is_over():
        if verbose:
            print("\n" + board.render())
            print(f"{NAMES[board.player]} must play in {describe_target(board)}.")
        player = players[board.player]
        start = time.monotonic()
        if isinstance(player, MinimaxAI):
            result = player.search(board)
            move = result.move
            if verbose:
                row, col = to_global(move)
                print(
                    f"AI ({NAMES[board.player]}) plays {row + 1} {col + 1} "
                    f"[depth {result.depth}, {result.nodes} nodes, {time.monotonic() - start:.2f}s]"
                )
        else:
            move = player.choose_move(board)
        board.play(move)
    if verbose:
        print("\n" + board.render())
        print("Draw." if board.winner == DRAW else f"{NAMES[board.winner]} wins!")
    return board.winner


def benchmark(games: int, time_limit: float) -> None:
    wins = draws = losses = 0
    for g in range(games):
        ai, opponent = MinimaxAI(time_limit=time_limit), RandomAI(seed=g)
        ai_side = X if g % 2 == 0 else O
        winner = play_game(ai if ai_side == X else opponent, opponent if ai_side == X else ai, verbose=False)
        if winner == ai_side:
            wins += 1
        elif winner == DRAW:
            draws += 1
        else:
            losses += 1
    print(f"AI vs random over {games} games ({time_limit}s per move): {wins} wins, {draws} draws, {losses} losses")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ultimate Tic Tac Toe with a minimax AI.")
    parser.add_argument("--x", choices=["human", "ai", "random"], default="human", help="who plays X (moves first)")
    parser.add_argument("--o", choices=["human", "ai", "random"], default="ai", help="who plays O")
    parser.add_argument("--time", type=float, default=1.0, help="AI thinking time per move, in seconds")
    parser.add_argument("--bench", type=int, metavar="N", help="play N games of AI vs random and print the score")
    args = parser.parse_args()

    if args.bench:
        benchmark(args.bench, args.time)
    else:
        try:
            play_game(make_player(args.x, args.time), make_player(args.o, args.time))
        except (EOFError, KeyboardInterrupt):
            print("\nGame aborted.")


if __name__ == "__main__":
    main()
