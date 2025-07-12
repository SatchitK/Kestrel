from .search import find_best_move
from .book import Book
import time

BOOK = Book("gm2600.bin")

def best_move(board, time_limit=2.0):
    if board.fullmove_number <= 12:
        bm = BOOK.lookup(board)
        if bm:
            return bm
    return find_best_move(board, time_limit)

from .uci import UciEngine
Engine = UciEngine
