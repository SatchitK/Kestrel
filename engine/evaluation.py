# import chess

# VAL = {
#     chess.PAWN:   100,
#     chess.KNIGHT: 320,
#     chess.BISHOP: 330,
#     chess.ROOK:   500,
#     chess.QUEEN:  900,
#     chess.KING:     0
# }

# PST = {
#     chess.PAWN: [
#          0,   5,   5,  -5,  -5,  10,  50,   0,
#          0,  10,  -5,   0,   0,  10,  50,   0,
#          0,  10, -10,  20,  25,  30,  50,   0,
#          0, -20,   0,   0,  25,  30,  50,   0,
#          0,  10,  -5,   0,  25,  30,  50,   0,
#          0,  10,  -5,   0,   0,  10,  50,   0,
#          0,  10, -10,  -5,  -5,  10,  50,   0,
#          0,   5,   5,  -5,  -5,  10,  50,   0],
#     chess.KNIGHT: [
#        -50, -40, -30, -30, -30, -30, -40, -50,
#        -40, -20,   0,   0,   0,   0, -20, -40,
#        -30,   0,  10,  15,  15,  10,   0, -30,
#        -30,   5,  15,  20,  20,  15,   5, -30,
#        -30,   0,  15,  20,  20,  15,   0, -30,
#        -30,   5,  10,  15,  15,  10,   5, -30,
#        -40, -20,   0,   5,   5,   0, -20, -40,
#        -50, -40, -30, -30, -30, -30, -40, -50],
#     chess.BISHOP: [
#        -20, -10, -10, -10, -10, -10, -10, -20,
#        -10,   5,   0,   0,   0,   0,   5, -10,
#        -10,  10,  10,  10,  10,  10,  10, -10,
#        -10,   0,  10,  10,  10,  10,   0, -10,
#        -10,   5,   5,  10,  10,   5,   5, -10,
#        -10,   0,   5,  10,  10,   5,   0, -10,
#        -10,   0,   0,   0,   0,   0,   0, -10,
#        -20, -10, -10, -10, -10, -10, -10, -20],
#     chess.ROOK: [
#          0,   0,   5,  10,  10,   5,   0,   0,
#          0,   0,   5,  10,  10,   5,   0,   0,
#          0,   0,   5,  10,  10,   5,   0,   0,
#          0,   0,   5,  10,  10,   5,   0,   0,
#          0,   0,   5,  10,  10,   5,   0,   0,
#          0,   0,   5,  10,  10,   5,   0,   0,
#         25,  25,  25,  25,  25,  25,  25,  25,
#          0,   0,   5,  10,  10,   5,   0,   0],
#     chess.QUEEN: [
#        -20, -10, -10,  -5,  -5, -10, -10, -20,
#        -10,   0,   0,   0,   0,   0,   0, -10,
#        -10,   0,   5,   5,   5,   5,   0, -10,
#         -5,   0,   5,   5,   5,   5,   0,  -5,
#          0,   0,   5,   5,   5,   5,   0,  -5,
#        -10,   5,   5,   5,   5,   5,   0, -10,
#        -10,   0,   5,   0,   0,   0,   0, -10,
#        -20, -10, -10,  -5,  -5, -10, -10, -20],
#     chess.KING: [
#        -30, -40, -40, -50, -50, -40, -40, -30,
#        -30, -40, -40, -50, -50, -40, -40, -30,
#        -30, -40, -40, -50, -50, -40, -40, -30,
#        -30, -40, -40, -50, -50, -40, -40, -30,
#        -20, -30, -30, -40, -40, -30, -30, -20,
#        -10, -20, -20, -20, -20, -20, -20, -10,
#         20,  20,   0,   0,   0,   0,  20,  20,
#         20,  30,  10,   0,   0,  10,  30,  20]
# }

# def passed_pawn_bonus(board: chess.Board) -> int:
#     side      = board.turn
#     my_pawns  = board.pieces(chess.PAWN, side)
#     opp_pawns = board.pieces(chess.PAWN, not side)
#     bonus     = 0

#     for sq in my_pawns:
#         f   = chess.square_file(sq)
#         r   = chess.square_rank(sq)
#         blocked = False
#         for df in (-1, 0, 1):
#             nf = f + df
#             if not 0 <= nf <= 7:
#                 continue
#             if side == chess.WHITE:
#                 ahead = (chess.square(nf, nr) for nr in range(r + 1, 8))
#             else:
#                 ahead = (chess.square(nf, nr) for nr in range(r - 1, -1, -1))
#             if any(sq2 in opp_pawns for sq2 in ahead):
#                 blocked = True
#                 break
#         if blocked:
#             continue

#         rank_from_white = r if side == chess.WHITE else 7 - r
#         bonus += (rank_from_white + 1) * 10
#     return bonus

# def _adjacent_file_has_pawn(file_idx: int, pawn_bb: chess.SquareSet) -> bool:
#     if file_idx > 0  and pawn_bb & chess.BB_FILES[file_idx - 1]:
#         return True
#     if file_idx < 7 and pawn_bb & chess.BB_FILES[file_idx + 1]:
#         return True
#     return False

# def king_safety(board: chess.Board) -> int:
#     if board.fullmove_number < 10:
#         return 0
#     k_sq = board.king(board.turn)
#     if k_sq is None:
#         return 0
#     file = chess.square_file(k_sq)
#     return -25 if file in (3, 4) else 0

# def evaluate(board: chess.Board) -> int:
#     score = 0

#     for sq, piece in board.piece_map().items():
#         val  = VAL[piece.piece_type]
#         pst  = PST[piece.piece_type][sq if piece.color else chess.square_mirror(sq)]
#         term = val + pst
#         score += term if piece.color == board.turn else -term

#     score += 4 * board.legal_moves.count()
#     board.turn = not board.turn
#     score -= 4 * board.legal_moves.count()
#     board.turn = not board.turn

#     score += passed_pawn_bonus(board)
#     score += king_safety(board)

#     return score


"""
engine/evaluation.py
Classic hand-crafted evaluation (~2 100 Elo in 5-s games)

All scores are centipawns and returned **from the point of view of the
side to move** (positive = better for the side to move).
"""
from __future__ import annotations
import chess

# ───────────────────────────────────────────────────────────────
# 1.  STATIC VALUES & TABLES
# ───────────────────────────────────────────────────────────────
VAL = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:     0,          # king material is treated elsewhere
}

# 64-square mid-game piece-square tables (white point of view; mirror for black)
# Generated from early Crafty / Sunfish tables and tweaked for this engine
# Each list **must** contain exactly 64 integers.
PST_MG = {
    chess.PAWN: [
         0,   5,   5,  -5,  -5,  10,  50,   0,
         0,  10, -10,   0,   0,  10,  50,   0,
         0,  10, -10,  20,  25,  30,  50,   0,
         0, -20,   0,   0,  25,  30,  50,   0,
         0,  10, -10,   0,  25,  30,  50,   0,
         0,  10, -10,   0,   0,  10,  50,   0,
         0,  10, -10,  -5,  -5,  10,  50,   0,
         0,   5,   5,  -5,  -5,  10,  50,   0],
    chess.KNIGHT: [
       -50, -40, -30, -30, -30, -30, -40, -50,
       -40, -25,  -5,  -5,  -5,  -5, -25, -40,
       -30,  -5,  10,  15,  15,  10,  -5, -30,
       -30,   0,  15,  20,  20,  15,   0, -30,
       -30,   0,  15,  20,  20,  15,   0, -30,
       -30,  -5,  10,  15,  15,  10,  -5, -30,
       -40, -25,  -5,   0,   0,  -5, -25, -40,
       -50, -40, -30, -30, -30, -30, -40, -50],
    chess.BISHOP: [
       -20, -10, -10, -10, -10, -10, -10, -20,
       -10,   5,   0,   0,   0,   0,   5, -10,
       -10,  10,  10,  10,  10,  10,  10, -10,
       -10,   0,  10,  15,  15,  10,   0, -10,
       -10,   5,   5,  15,  15,   5,   5, -10,
       -10,   0,   5,  10,  10,   5,   0, -10,
       -10,   0,   0,   0,   0,   0,   0, -10,
       -20, -10, -10, -10, -10, -10, -10, -20],
    chess.ROOK: [
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
        10,  10,  10,  10,  10,  10,  10,  10,
        25,  25,  25,  25,  25,  25,  25,  25,
         0,   0,   5,  10,  10,   5,   0,   0],
    chess.QUEEN: [
       -20, -10, -10,  -5,  -5, -10, -10, -20,
       -10,   0,   0,   0,   0,   0,   0, -10,
       -10,   0,  10,  10,  10,  10,   0, -10,
        -5,   0,  10,  10,  10,  10,   0,  -5,
         0,   0,  10,  10,  10,  10,   0,  -5,
       -10,  10,  10,  10,  10,  10,   0, -10,
       -10,   0,  10,   0,   0,   0,   0, -10,
       -20, -10, -10,  -5,  -5, -10, -10, -20],
    chess.KING: [
       -30, -40, -40, -50, -50, -40, -40, -30,
       -30, -40, -40, -50, -50, -40, -40, -30,
       -30, -40, -40, -50, -50, -40, -40, -30,
       -30, -40, -40, -50, -50, -40, -40, -30,
       -20, -30, -30, -40, -40, -30, -30, -20,
       -10, -20, -20, -20, -20, -20, -20, -10,
        20,  20,   0,   0,   0,   0,  20,  20,
        20,  30,  10,   0,   0,  10,  30,  20],
}

# all end-game PSTs = 0  (king safety dominates late phases)
PST_EG = {pt: [0]*64 for pt in PST_MG}

# ───────────────────────────────────────────────────────────────
# 2.  SMALL UTILITIES
# ───────────────────────────────────────────────────────────────
PHASE_UNIT = {chess.PAWN:0, chess.KNIGHT:1, chess.BISHOP:1,
              chess.ROOK:2, chess.QUEEN:4, chess.KING:0}
START_PHASE = 24                    # full material score

def _piece_index(sq: int, colour: bool) -> int:
    """Return table index for side-to-move viewpoint."""
    return sq if colour else chess.square_mirror(sq)

# ───────────────────────────────────────────────────────────────
# 3.  SUB-SCORES
# ───────────────────────────────────────────────────────────────
def _passed_pawns(board: chess.Board, colour: bool) -> int:
    pawns_my  = int(board.pieces(chess.PAWN, colour))
    pawns_opp = int(board.pieces(chess.PAWN, not colour))
    bonus = 0

    bb = pawns_my
    while bb:
        sq_bb = bb & -bb                       # 1) LS1B mask
        sq    = sq_bb.bit_length() - 1         # 2) index 0-63
        bb   ^= sq_bb                          # 3) pop bit

        file = chess.square_file(sq)
        mask_front = chess.BB_FILES[file]

        if colour:                             # white pawns go north
            front = mask_front & ~((1 << (sq + 1)) - 1)
        else:                                  # black pawns go south
            front = mask_front & ((1 << sq) - 1)

        side_files = chess.BB_FILES[max(0, file - 1)] | \
                     chess.BB_FILES[min(7, file + 1)]

        if (front | (front & side_files)) & pawns_opp:
            continue                           # not passed

        rank = chess.square_rank(sq) if colour else 7 - chess.square_rank(sq)
        bonus += 20 + rank * 5                 # rank-scaled
    return bonus

def _pawn_structure(board: chess.Board, colour: bool) -> int:
    my = int(board.pieces(chess.PAWN, colour))
    if not my:
        return 0
    files = [(my & chess.BB_FILES[f]) for f in range(8)]
    score = 0
    for f, bb in enumerate(files):
        cnt = bb.bit_count()
        if cnt > 1:
            score -= 8*(cnt-1)      # doubled/tripled
        if not (f and files[f-1]) and not (f==7 or files[f+1]):
            score -= 10             # isolated
    return score

def _rook_queen_activity(board: chess.Board, colour: bool) -> int:
    pawns = int(board.pieces(chess.PAWN, chess.WHITE) |
                board.pieces(chess.PAWN, chess.BLACK))
    bonus = 0
    for sq in board.pieces(chess.ROOK, colour) | board.pieces(chess.QUEEN, colour):
        file = chess.square_file(sq)
        file_mask = chess.BB_FILES[file]
        if not (file_mask & pawns):
            bonus += 10             # open file
        elif not (file_mask & board.occupied_co[colour]):
            bonus += 5              # semi-open
    return bonus

def _bishop_pair(board: chess.Board, colour: bool) -> int:
    return 30 if len(board.pieces(chess.BISHOP, colour)) == 2 else 0

def _king_safety(board: chess.Board, colour: bool) -> int:
    ksq = board.king(colour)
    if ksq is None:
        return 0
    # missing pawn shield
    file = chess.square_file(ksq)
    rankside = 1 if colour else 6
    shield = 0
    for f in (file-1, file, file+1):
        if 0 <= f <= 7:
            if board.piece_type_at(chess.square(f, rankside)) != chess.PAWN or \
               board.color_at(chess.square(f, rankside)) != colour:
                shield += 1
    # enemy attackers
    attackers = len(board.attackers(not colour, ksq))
    return -(15*shield + 4*attackers)

# ───────────────────────────────────────────────────────────────
# 4.  MAIN STATIC EVALUATION
# ───────────────────────────────────────────────────────────────
def evaluate(board: chess.Board) -> int:
    # material & PST
    mg_my = mg_opp = eg_my = eg_opp = 0
    phase = START_PHASE
    for sq, piece in board.piece_map().items():
        idx = _piece_index(sq, piece.color)
        val = VAL[piece.piece_type]
        mg_val = val + PST_MG[piece.piece_type][idx]
        eg_val = val + PST_EG[piece.piece_type][idx]
        if piece.color == board.turn:
            mg_my += mg_val
            eg_my += eg_val
        else:
            mg_opp += mg_val
            eg_opp += eg_val
        phase -= PHASE_UNIT[piece.piece_type]

    # side-dependent extras
    col = board.turn
    extras_my  = (_bishop_pair(board, col) +
                  _passed_pawns(board, col) +
                  _pawn_structure(board, col) +
                  _rook_queen_activity(board, col) +
                  _king_safety(board, col))
    extras_opp = (_bishop_pair(board, not col) +
                  _passed_pawns(board, not col) +
                  _pawn_structure(board, not col) +
                  _rook_queen_activity(board, not col) +
                  _king_safety(board, not col))

    mg_score = mg_my - mg_opp + extras_my - extras_opp
    eg_score = eg_my - eg_opp + extras_my - extras_opp

    if phase < 0:
        phase = 0
    score = (mg_score * phase + eg_score * (START_PHASE - phase)) // START_PHASE

    # simple mobility (scaled)
    mob_my  = board.legal_moves.count()
    board.turn = not board.turn
    mob_opp = board.legal_moves.count()
    board.turn = not board.turn
    score += 4 * (mob_my - mob_opp)

    return score
