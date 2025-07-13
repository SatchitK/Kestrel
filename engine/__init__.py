# from .search import find_best_move
# from .book import Book
# import time

# BOOK = Book("engine/komodo.bin")

# def best_move(board, time_limit=2.0):
#     if board.fullmove_number <= 12:  # Opening phase
#         bm = BOOK.lookup(board)
#         if bm:
#             print(f"[ENGINE] Using book move: {bm}")
#             return bm
#     print("[ENGINE] Falling back to engine search.")
#     return find_best_move(board, time_limit)

# from .uci import UciEngine
# Engine = UciEngine


from .search import find_best_move
from .book import Book
from .see import see          # <-- keeps module visible for others if needed

import time

BOOK = Book("engine/komodo.bin")


def best_move(board, time_limit: float = 2.0):
    if board.fullmove_number <= 12:        # opening phase
        bm = BOOK.lookup(board)
        if bm:
            print(f"[ENGINE] Using book move: {bm}")
            return bm
    print("[ENGINE] Falling back to engine search.")
    return find_best_move(board, time_limit)


from .uci import UciEngine
Engine = UciEngine
