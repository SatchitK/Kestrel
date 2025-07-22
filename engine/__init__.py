from .search import find_best_move
from .book import Book
from .see import see # <-- keeps module visible for others if needed
import time
import chess # Added for board handling

BOOK = Book("engine/komodo.bin")

def best_move(board: chess.Board, time_limit: float = 10.0): # <-- CHANGED
    """
    Finds the best move for a given board position.
    The default time_limit has been increased to 10 seconds.
    """
    if board.fullmove_number <= 12: # opening phase
        bm = BOOK.lookup(board)
        if bm:
            print(f"[ENGINE] Using book move: {bm}")
            return bm
    
    print("[ENGINE] Falling back to engine search.")
    return find_best_move(board, time_limit)

from .uci import UciEngine
Engine = UciEngine
