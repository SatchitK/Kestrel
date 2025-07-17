import struct, os, random, chess
from .transposition import zobrist_hash
import chess.polyglot

class Book:
    def __init__(self, file="book.bin"):
        self.entries = []
        if os.path.exists(file):
            with open(file, "rb") as f:
                data = f.read()
            for i in range(0, len(data), 16):
                key, move, weight, learn = struct.unpack(">QHHI", data[i:i+16])
                self.entries.append((key, move, weight))
            print(f"[BOOK] Loaded {len(self.entries)} entries from {file}.")
        else:
            print(f"[BOOK] File {file} not found.")

    def lookup(self, board: chess.Board):
        if not self.entries:
            print("[BOOK] No entries loaded in the book.")
            return None

        # Use python-chess's Polyglot-compatible hashing for book lookups
        key = chess.polyglot.zobrist_hash(board)
        moves = [(m, w) for k, m, w in self.entries if k == key]
        if not moves:
            print("[BOOK] No moves found for the current position in the book.")
            # Fall back to engine logic using zobrist_hash (improved: log hash)
            engine_key = zobrist_hash(board)
            print(f"[ENGINE] Using Zobrist hash for engine evaluation: {engine_key}")
            return None

        total_weight = sum(w for _, w in moves)
        r = random.randrange(total_weight)
        cumulative_weight = 0
        for move16, weight in moves:
            cumulative_weight += weight
            if r < cumulative_weight:
                move = chess.Move.from_uci(polyglot_move_to_uci(move16))
                print(f"[BOOK] Found move: {move}")
                return move
        print("[BOOK] Failed to select a move from the book.")
        return None

def polyglot_move_to_uci(move16):
    from_sq = (move16 >> 6) & 0x3F
    to_sq = move16 & 0x3F
    prom = (move16 >> 12) & 0x7
    uci = chess.square_name(from_sq) + chess.square_name(to_sq)
    if prom:
        uci += " nbrq"[prom]
    return uci
