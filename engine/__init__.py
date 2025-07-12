"""
Kestrel-Engine  ▸ minimalist classical-AI chess engine (~2000 Elo)

Exposes:
    best_move(board, time_limit)  – main search entry
    Engine                          – UCI driver (optional)
"""
from .search import find_best_move
from .book import Book
import time

BOOK = Book("gm2600.bin")     # uses your GM-2600 Polyglot book
      # tiny polyglot book (optional, can be empty)

def best_move(board, time_limit=2.0):
    """
    Return best move for the given python-chess Board.
    Uses opening book first, then iterative deepening search.
    """
    # 1 ▸ book move if position found and within first 12 plies
    if board.fullmove_number <= 12:
        bm = BOOK.lookup(board)
        if bm:
            return bm

    # 2 ▸ otherwise search
    return find_best_move(board, time_limit)

# ───────────────────────────────────────────────────────────────
# UCI front-end (optional, allows testing in GUI arenas)
from .uci import UciEngine
Engine = UciEngine
