from __future__ import annotations
import mmap, random, struct, chess

_rng = random.Random(42)
Z_KEYS = [[_rng.getrandbits(64) for _ in range(12)] for _ in range(64)]
Z_BLACK = _rng.getrandbits(64)
Z_CASTLING = [_rng.getrandbits(64) for _ in range(16)]
Z_EP = [_rng.getrandbits(64) for _ in range(8)]

def zobrist_hash(b: chess.Board) -> int:
    h = 0
    for sq, pc in b.piece_map().items():
        h ^= Z_KEYS[sq][pc.piece_type - 1 + (6 if pc.color == chess.BLACK else 0)]
    if b.turn == chess.BLACK: h ^= Z_BLACK
    
    cr_index = ( (1 if b.has_kingside_castling_rights(chess.WHITE) else 0) |
                 (2 if b.has_queenside_castling_rights(chess.WHITE) else 0) |
                 (4 if b.has_kingside_castling_rights(chess.BLACK) else 0) |
                 (8 if b.has_queenside_castling_rights(chess.BLACK) else 0) )
    h ^= Z_CASTLING[cr_index]
    
    if b.ep_square is not None: h ^= Z_EP[chess.square_file(b.ep_square)]
    return h

# --- Transposition Table ---
EXACT, LOWER, UPPER = 0, 1, 2
TT_SIZE = 1 << 24 # 16M entries
TT_MASK = TT_SIZE - 1

# CORRECTED STRUCT: score is now 'i' (4-byte int), depth and flag are packed into one 'H'
# Total size is 8 (key) + 4 (score) + 2 (depth/flag) + 2 (move) = 16 bytes.
_SLOT = struct.Struct("=Q i H H") 
EMPTY = _SLOT.pack(0, 0, 0, 0)

_table = mmap.mmap(-1, TT_SIZE * _SLOT.size, access=mmap.ACCESS_WRITE)
_table[:] = EMPTY * TT_SIZE

def pack_move(move: chess.Move | None) -> int:
    if move is None: return 0
    return (move.from_square << 10) | (move.to_square << 4) | (move.promotion or 0)

def unpack_move(board: chess.Board, move_int: int) -> chess.Move | None:
    if move_int == 0: return None
    from_sq = (move_int >> 10) & 0x3F
    to_sq = (move_int >> 4) & 0x3F
    promotion = move_int & 0xF
    try:
        return chess.Move(from_sq, to_sq, promotion=promotion if promotion else None)
    except ValueError:
        return None

def probe(key: int) -> tuple | None:
    off = (key & TT_MASK) * _SLOT.size
    k, s, df, mv_int = _SLOT.unpack_from(_table, off)
    if k == key:
        depth = df >> 2
        flag = df & 0x03
        return depth, s, flag, mv_int
    return None

def store(key: int, depth: int, score: int, flag: int, move: chess.Move):
    off = (key & TT_MASK) * _SLOT.size
    # Pack depth and flag together into a 16-bit integer
    depth_and_flag = (depth << 2) | flag
    _SLOT.pack_into(_table, off, key, score, depth_and_flag, pack_move(move))
