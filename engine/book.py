import struct, os, random, chess
from .transposition import zobrist_hash

class Book:
    def __init__(self, file="book.bin"):
        self.entries = []
        if os.path.exists(file):
            with open(file, "rb") as f:
                data = f.read()
            for i in range(0, len(data), 16):
                key, move, weight, learn = struct.unpack(">QHHI", data[i:i+16])
                self.entries.append((key, move, weight))

    def lookup(self, board: chess.Board):
        if not self.entries:
            return None
        key = zobrist_hash(board)
        moves = [(m, w) for k, m, w in self.entries if k == key]
        if not moves:
            return None
        total = sum(w for _, w in moves)
        r = random.randrange(total)
        cum = 0
        for move16, weight in moves:
            cum += weight
            if r < cum:
                return chess.Move.from_uci(polyglot_move_to_uci(move16))
        return None

def polyglot_move_to_uci(move16):
    from_sq = (move16 >> 6) & 0x3F
    to_sq   = move16 & 0x3F
    prom    = (move16 >> 12) & 0x7
    uci = chess.square_name(from_sq) + chess.square_name(to_sq)
    if prom:
        uci += " nbrq"[prom]
    return uci
