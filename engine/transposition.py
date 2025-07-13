# import random
# import chess

# Z_KEYS = [[random.getrandbits(64) for _ in range(12)] for _ in range(64)]
# Z_BLACK = random.getrandbits(64)
# Z_CASTLING = [random.getrandbits(64) for _ in range(16)]
# Z_EP = [random.getrandbits(64) for _ in range(8)]

# def zobrist_hash(board: chess.Board):
#     h = 0
#     for sq, piece in board.piece_map().items():
#         idx = piece.piece_type - 1 + (0 if piece.color == chess.WHITE else 6)
#         h ^= Z_KEYS[sq][idx]
#     if board.turn == chess.BLACK:
#         h ^= Z_BLACK
#     rights = 0
#     if board.has_kingside_castling_rights(chess.WHITE):  rights |= 1
#     if board.has_queenside_castling_rights(chess.WHITE): rights |= 2
#     if board.has_kingside_castling_rights(chess.BLACK):  rights |= 4
#     if board.has_queenside_castling_rights(chess.BLACK): rights |= 8
#     h ^= Z_CASTLING[rights]
#     if board.ep_square is not None:
#         h ^= Z_EP[chess.square_file(board.ep_square)]
#     return h

# def polyglot_hash(board: chess.Board) -> int:
#         h = 0
#         for sq, piece in board.piece_map().items():
#             piece_idx = piece.piece_type - 1 + (0 if piece.color == chess.WHITE else 6)
#             h ^= Z_KEYS[sq][piece_idx]
#         if board.turn == chess.BLACK:
#             h ^= Z_BLACK
#         rights = (
#             (1 if board.has_kingside_castling_rights(chess.WHITE) else 0) |
#             (2 if board.has_queenside_castling_rights(chess.WHITE) else 0) |
#             (4 if board.has_kingside_castling_rights(chess.BLACK) else 0) |
#             (8 if board.has_queenside_castling_rights(chess.BLACK) else 0)
#         )
#         h ^= Z_CASTLING[rights]
#         if board.ep_square is not None:
#             h ^= Z_EP[chess.square_file(board.ep_square)]
#         return h

# TT_SIZE = 1 << 20
# TT_MASK = TT_SIZE - 1

# EXACT, LOWER, UPPER = 0, 1, 2

# class TTEntry:
#     __slots__ = ("key", "depth", "score", "flag", "move")
#     def __init__(self, key=0, depth=0, score=0, flag=0, move=None):
#         self.key, self.depth, self.score, self.flag, self.move = \
#             key, depth, score, flag, move

# TT = [TTEntry() for _ in range(TT_SIZE)]

# def probe(hash_key):
#     entry = TT[hash_key & TT_MASK]
#     return entry if entry.key == hash_key else None

# def store(hash_key, depth, score, flag, move):
#     idx = hash_key & TT_MASK
#     e = TT[idx]
#     if depth > e.depth or flag == EXACT:
#         TT[idx] = TTEntry(hash_key, depth, score, flag, move)


"""
engine/transposition.py  •  2-tier transposition table
STD hash replacement:  first by depth, then prefer EXACT over bounds.
"""
from __future__ import annotations
import random, chess

# ───────────────────────── zobrist hash ─────────────────────────
rng = random.Random(2025)                                # reproducible
Z_KEYS = [[rng.getrandbits(64) for _ in range(12)] for _ in range(64)]
Z_BLACK = rng.getrandbits(64)
Z_CASTLING = [rng.getrandbits(64) for _ in range(16)]
Z_EP = [rng.getrandbits(64) for _ in range(8)]


def zobrist_hash(board: chess.Board) -> int:
    h = 0
    for sq, pc in board.piece_map().items():
        idx = pc.piece_type - 1 + (0 if pc.color else 6)
        h ^= Z_KEYS[sq][idx]
    if board.turn == chess.BLACK:
        h ^= Z_BLACK
    rights = ((1 if board.has_kingside_castling_rights(chess.WHITE) else 0) |
              (2 if board.has_queenside_castling_rights(chess.WHITE) else 0) |
              (4 if board.has_kingside_castling_rights(chess.BLACK) else 0) |
              (8 if board.has_queenside_castling_rights(chess.BLACK) else 0))
    h ^= Z_CASTLING[rights]
    if board.ep_square is not None:
        h ^= Z_EP[chess.square_file(board.ep_square)]
    return h

# ───────────────────────── table structs ────────────────────────
EXACT, LOWER, UPPER = 0, 1, 2
TT_SIZE = 1 << 22                # 4 M entries  ≈ 128 MB
TT_MASK = TT_SIZE - 1


class TTEntry:
    __slots__ = ("key", "depth", "score", "flag", "move")

    def __init__(self, key=0, depth=0, score=0, flag=0, move=None):
        self.key, self.depth, self.score, self.flag, self.move = \
            key, depth, score, flag, move


_primary = [TTEntry() for _ in range(TT_SIZE)]
_secondary = [TTEntry() for _ in range(TT_SIZE)]         # fall-back bucket


def probe(key: int) -> TTEntry | None:
    e = _primary[key & TT_MASK]
    if e.key == key:
        return e
    e2 = _secondary[key & TT_MASK]
    return e2 if e2.key == key else None


def store(key: int, depth: int, score: int, flag: int, move):
    idx = key & TT_MASK
    slot = _primary[idx]
    if (slot.key != key and depth > slot.depth) or flag == EXACT:
        _secondary[idx] = slot                         # demote old primary
        _primary[idx] = TTEntry(key, depth, score, flag, move)
