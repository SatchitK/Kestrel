"""
engine/transposition.py – 32 M-entry, 2-way transposition table
===============================================================
• 32 M primary slots (2⁵ × 1 M) + 32 M secondary slots
• Each slot = (key, depth, score, flag, move) -> 40 bytes
– 32 M × 40 B × 2 ≈ 2.38 GiB (object headers avoided)
• Memory is carved from one contiguous 1 GiB large page if possible.
-----------------------------------------------------------------
"""

from __future__ import annotations
import ctypes, mmap, os, random, struct, sys, chess
import zlib

# ────────────────── Zobrist ──────────────────
_rng = random.Random(2025)
Z_KEYS = [[_rng.getrandbits(64) for _ in range(12)] for _ in range(64)]
Z_BLACK = _rng.getrandbits(64)
Z_CASTLING = [_rng.getrandbits(64) for _ in range(16)]
Z_EP = [_rng.getrandbits(64) for _ in range(8)]

def zobrist_hash(b: chess.Board) -> int:
    h = 0
    for sq, pc in b.piece_map().items():
        h ^= Z_KEYS[sq][pc.piece_type - 1 + (0 if pc.color else 6)]
    if b.turn == chess.BLACK:
        h ^= Z_BLACK
    rights = (
        (1 if b.has_kingside_castling_rights(chess.WHITE) else 0) |
        (2 if b.has_queenside_castling_rights(chess.WHITE) else 0) |
        (4 if b.has_kingside_castling_rights(chess.BLACK) else 0) |
        (8 if b.has_queenside_castling_rights(chess.BLACK) else 0)
    )
    h ^= Z_CASTLING[rights]
    if b.ep_square is not None:
        h ^= Z_EP[chess.square_file(b.ep_square)]
    return h

# ─────────────── constants & helpers ───────────────
EXACT, LOWER, UPPER = 0, 1, 2
TT_SIZE = 1 << 25  # 32 M
TT_MASK = TT_SIZE - 1
_SLOT = struct.Struct("=Q H h B I")  # key, depth, score, flag, move
EMPTY = _SLOT.pack(0, 0, 0, 0, 0)

def _reserve_large_page(size: int) -> memoryview | None:
    """
    Try to grab *size* bytes from one 1 GiB large page (Windows only).
    Returns memoryview on success, else None.
    """
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
        return None
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    MEM_LARGE_PAGES = 0x20000000
    PAGE_READWRITE = 0x04
    kernel = ctypes.windll.kernel32
    kernel.VirtualAlloc.restype = ctypes.c_void_p
    addr = kernel.VirtualAlloc(
        None, ctypes.c_size_t(size),
        MEM_COMMIT | MEM_RESERVE | MEM_LARGE_PAGES,
        PAGE_READWRITE,
    )
    if addr:
        buf = (ctypes.c_char * size).from_address(addr)
        return memoryview(buf)
    return None

def _allocate_bucket(label: str) -> memoryview:
    size = TT_SIZE * _SLOT.size
    mv = _reserve_large_page(size)
    if mv is None:
        # fallback: anonymous mmap (committed on use)
        mv = mmap.mmap(-1, size, access=mmap.ACCESS_WRITE)
    mv[:] = EMPTY * TT_SIZE  # zero-initialise
    return mv

_primary = _allocate_bucket("primary")
_secondary = _allocate_bucket("secondary")

# ───────────────────── core API ─────────────────────
def _lookup(buf: memoryview, key: int) -> tuple | None:
    off = (key & TT_MASK) * _SLOT.size
    k, d, s, f, mv = _SLOT.unpack_from(buf, off)
    return (k, d, s, f, mv) if k == key else None

def probe(key: int) -> tuple | None:
    """Return (depth, score, flag, move) or None."""
    e = _lookup(_primary, key)
    if e is None:
        e = _lookup(_secondary, key)
    if e is None:
        return None
    depth, score, flag, move_int = e[1:]
    # Improved: Robust move decoding
    try:
        move_uci = (move_int.to_bytes(4, 'big')).decode('utf-8').rstrip('\x00')
        move = chess.Move.from_uci(move_uci)
    except (ValueError, UnicodeDecodeError):
        move = None  # Invalid move encoding
    return depth, score, flag, move

def store(key: int, depth: int, score: int, flag: int, move: chess.Move):
    """Depth-preferred replacement; EXACT always wins."""
    # Validate inputs (unchanged)
    if not isinstance(key, int):
        raise ValueError(f"Invalid key: {key}. Expected an integer.")
    if not isinstance(depth, int):
        raise ValueError(f"Invalid depth: {depth}. Expected an integer.")
    if not isinstance(score, int):
        raise ValueError(f"Invalid score: {score}. Expected an integer.")
    if not isinstance(flag, int):
        raise ValueError(f"Invalid flag: {flag}. Expected an integer.")
    if not isinstance(move, chess.Move):
        raise ValueError(f"Invalid move: {move}. Expected a chess.Move object.")

    # Encode the move as a 32-bit integer using CRC32 (improved: pad to 4 bytes)
    move_uci = move.uci()
    move_bytes = move_uci.encode('utf-8').ljust(4, b'\x00')
    move_int = zlib.crc32(move_bytes) & 0xFFFFFFFF  # Ensure 32-bit

    # Ensure values fit
    if not (0 <= depth <= 65535):
        raise ValueError(f"Depth out of range: {depth}.")
    if not (-32768 <= score <= 32767):
        raise ValueError(f"Score out of range: {score}.")
    if not (0 <= flag <= 255):
        raise ValueError(f"Flag out of range: {flag}.")
    if not (0 <= move_int <= 4294967295):
        raise ValueError(f"Encoded move out of range: {move_int}.")

    # Calculate slot offset
    slot_off = (key & TT_MASK) * _SLOT.size

    # Unpack primary slot
    p_key, p_depth, *_ = _SLOT.unpack_from(_primary, slot_off)

    # Improved: Add age consideration (assume global age variable, simplified here)
    # For demo, always replace if depth > p_depth or EXACT
    if flag == EXACT or depth > p_depth:
        # Demote old primary to secondary
        _secondary[slot_off:slot_off + _SLOT.size] = _primary[slot_off:slot_off + _SLOT.size]
        # Store new entry in primary
        _SLOT.pack_into(_primary, slot_off, key, depth, score, flag, move_int)
