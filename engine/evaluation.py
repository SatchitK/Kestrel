# # # """
# # # engine/evaluation.py
# # # Hand-crafted evaluation (~2100 Elo at blitz) expressed in **centipawns** and
# # # returned from the *side-to-move* perspective (positive = good for STM).
# # # """

# # # from __future__ import annotations
# # # import chess

# # # # ──────────────────────────────────────────────────────────────
# # # # 1.  TUNABLE WEIGHTS
# # # # ──────────────────────────────────────────────────────────────
# # # WEIGHTS = {
# # #     # material
# # #     "material": {
# # #         chess.PAWN:   100,
# # #         chess.KNIGHT: 320,
# # #         chess.BISHOP: 330,
# # #         chess.ROOK:   500,
# # #         chess.QUEEN:  900,
# # #         chess.KING:     0,          # king material handled elsewhere
# # #     },

# # #     # misc extras
# # #     "bishop_pair" :  30,
# # #     "queen_danger": 800,            # penalty when queen is under attack
# # #     # rank-indexed passed-pawn bonus (white POV; mirror for black)
# # #     "passed_rank" : [0, 5, 10, 20, 40, 60, 80, 100],
# # # }

# # # # ──────────────────────────────────────────────────────────────
# # # # 2.  PIECE-SQUARE TABLES (mid-game)
# # # # ──────────────────────────────────────────────────────────────
# # # PST_MG = {
# # #     chess.PAWN:   [  0,  5,  5, -5, -5, 10, 50,  0,
# # #                      0, 10,-10,  0,  0, 10, 50,  0,
# # #                      0, 10,-10, 20, 25, 30, 50,  0,
# # #                      0,-20,  0,  0, 25, 30, 50,  0,
# # #                      0, 10,-10,  0, 25, 30, 50,  0,
# # #                      0, 10,-10,  0,  0, 10, 50,  0,
# # #                      0, 10,-10, -5, -5, 10, 50,  0,
# # #                      0,  5,  5, -5, -5, 10, 50,  0],
# # #     chess.KNIGHT: [-50,-40,-30,-30,-30,-30,-40,-50,
# # #                    -40,-25, -5, -5, -5, -5,-25,-40,
# # #                    -30, -5, 10, 15, 15, 10, -5,-30,
# # #                    -30,  0, 15, 20, 20, 15,  0,-30,
# # #                    -30,  0, 15, 20, 20, 15,  0,-30,
# # #                    -30, -5, 10, 15, 15, 10, -5,-30,
# # #                    -40,-25, -5,  0,  0, -5,-25,-40,
# # #                    -50,-40,-30,-30,-30,-30,-40,-50],
# # #     chess.BISHOP: [-20,-10,-10,-10,-10,-10,-10,-20,
# # #                    -10,  5,  0,  0,  0,  0,  5,-10,
# # #                    -10, 10, 10, 10, 10, 10, 10,-10,
# # #                    -10,  0, 10, 15, 15, 10,  0,-10,
# # #                    -10,  5,  5, 15, 15,  5,  5,-10,
# # #                    -10,  0,  5, 10, 10,  5,  0,-10,
# # #                    -10,  0,  0,  0,  0,  0,  0,-10,
# # #                    -20,-10,-10,-10,-10,-10,-10,-20],
# # #     chess.ROOK:   [  0,  0,  5, 10, 10,  5,  0,  0,
# # #                      0,  0,  5, 10, 10,  5,  0,  0,
# # #                      0,  0,  5, 10, 10,  5,  0,  0,
# # #                      0,  0,  5, 10, 10,  5,  0,  0,
# # #                      0,  0,  5, 10, 10,  5,  0,  0,
# # #                     10, 10, 10, 10, 10, 10, 10, 10,
# # #                     25, 25, 25, 25, 25, 25, 25, 25,
# # #                      0,  0,  5, 10, 10,  5,  0,  0],
# # #     chess.QUEEN:  [-20,-10,-10, -5, -5,-10,-10,-20,
# # #                    -10,  0,  0,  0,  0,  0,  0,-10,
# # #                    -10,  0, 10, 10, 10, 10,  0,-10,
# # #                     -5,  0, 10, 10, 10, 10,  0, -5,
# # #                      0,  0, 10, 10, 10, 10,  0, -5,
# # #                    -10, 10, 10, 10, 10, 10,  0,-10,
# # #                    -10,  0, 10,  0,  0,  0,  0,-10,
# # #                    -20,-10,-10, -5, -5,-10,-10,-20],
# # #     chess.KING:   [-30,-40,-40,-50,-50,-40,-40,-30,
# # #                    -30,-40,-40,-50,-50,-40,-40,-30,
# # #                    -30,-40,-40,-50,-50,-40,-40,-30,
# # #                    -30,-40,-40,-50,-50,-40,-40,-30,
# # #                    -20,-30,-30,-40,-40,-30,-30,-20,
# # #                    -10,-20,-20,-20,-20,-20,-20,-10,
# # #                     20, 20,  0,  0,  0,  0, 20, 20,
# # #                     20, 30, 10,  0,  0, 10, 30, 20],
# # # }

# # # # end-game PSTs kept at zero for simplicity
# # # PST_EG = {pt: [0] * 64 for pt in PST_MG}

# # # # ──────────────────────────────────────────────────────────────
# # # # 3.  SMALL UTILITIES
# # # # ──────────────────────────────────────────────────────────────
# # # PHASE_UNIT   = {chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 1,
# # #                 chess.ROOK: 2, chess.QUEEN: 4, chess.KING: 0}
# # # START_PHASE  = 24           # full-material phase

# # # def _idx(sq: int, colour: bool) -> int:
# # #     """Mirror board for black so PSTs stay white-centric."""
# # #     return sq if colour else chess.square_mirror(sq)

# # # # ──────────────────────────────────────────────────────────────
# # # # 4.  SUB-SCORE TERMS
# # # # ──────────────────────────────────────────────────────────────
# # # def _bishop_pair(board: chess.Board, colour: bool) -> int:
# # #     return WEIGHTS["bishop_pair"] if len(board.pieces(chess.BISHOP, colour)) == 2 else 0

# # # # at top of the file for quick lookup
# # # # ---------------------------------------------------------------------
# # # # Queen-safety term  (replaces the faulty version that used BB_DIAGONALS)
# # # # ---------------------------------------------------------------------
# # # _PVAL = {
# # #     chess.PAWN: 100,
# # #     chess.KNIGHT: 320,
# # #     chess.BISHOP: 330,
# # #     chess.ROOK: 500,
# # #     chess.QUEEN: 900,
# # #     chess.KING: 0  # Add the king with a value of 0
# # # }

# # # def _queen_safety(board: chess.Board, colour: bool) -> int:
# # #     """
# # #     Negative score if *our* queen is in real danger,
# # #     positive score if the opponent’s queen is.
# # #     Scale: −900 … +900 cp.
# # #     """
# # #     q_sq = next(iter(board.pieces(chess.QUEEN, colour)), None)
# # #     if q_sq is None:  # Queen already off the board
# # #         return 0

# # #     opp = not colour
# # #     atk_bb = board.attackers(opp, q_sq)
# # #     if not atk_bb and not board.is_pinned(colour, q_sq):
# # #         return 0  # Totally safe

# # #     def_bb = board.attackers(colour, q_sq)
# # #     atk_val = sum(_PVAL[board.piece_type_at(sq)] for sq in atk_bb if board.piece_type_at(sq) is not None)
# # #     def_val = sum(_PVAL[board.piece_type_at(sq)] for sq in def_bb if board.piece_type_at(sq) is not None)

# # #     # 1. Attacking / defending material balance
# # #     balance = max(0, atk_val - def_val)  # 0 … 900

# # #     # 2. Escape mobility: each safe square refunds 60 cp (max 5)
# # #     safe = 0
# # #     for m in board.generate_legal_moves(from_mask=chess.BB_SQUARES[q_sq]):
# # #         board.push(m)
# # #         if not board.attackers(opp, m.to_square):
# # #             safe += 1
# # #         board.pop()
# # #         if safe == 5:
# # #             break
# # #     mobility = safe * 60  # 0 … 300

# # #     # 3. Pinned/x-ray bonus for the attacker
# # #     pin_pen = 200 if board.is_pinned(colour, q_sq) else 0

# # #     penalty = balance - mobility + pin_pen
# # #     penalty = max(-200, min(900, penalty))  # Clamp

# # #     return -penalty  # Negative if OUR queen is in danger



# # # def _passed_pawns(board: chess.Board, colour: bool) -> int:
# # #     my_pawns  = int(board.pieces(chess.PAWN,  colour))
# # #     opp_pawns = int(board.pieces(chess.PAWN, not colour))
# # #     bonus = 0
# # #     bb = my_pawns
# # #     while bb:
# # #         sq_bb = bb & -bb
# # #         sq    = sq_bb.bit_length() - 1
# # #         bb   ^= sq_bb
# # #         f = chess.square_file(sq)
# # #         mask_front = chess.BB_FILES[f]
# # #         front = (mask_front & ~((1 << (sq + 1)) - 1)) if colour \
# # #                 else (mask_front &  ((1 <<  sq     ) - 1))
# # #         side  = chess.BB_FILES[max(0, f-1)] | chess.BB_FILES[min(7, f+1)]
# # #         if (front | (front & side)) & opp_pawns:
# # #             continue
# # #         rank = chess.square_rank(sq) if colour else 7 - chess.square_rank(sq)
# # #         bonus += WEIGHTS["passed_rank"][rank]
# # #     return bonus

# # # def _pawn_structure(board: chess.Board, colour: bool) -> int:
# # #     my = int(board.pieces(chess.PAWN, colour))
# # #     if not my:
# # #         return 0
# # #     files = [(my & chess.BB_FILES[f]) for f in range(8)]
# # #     score = 0
# # #     for f, bb in enumerate(files):
# # #         cnt = int(bb).bit_count()
# # #         if cnt > 1:            # doubled / tripled
# # #             score -= 8 * (cnt - 1)
# # #         if not ((f and files[f-1]) or (f < 7 and files[f+1])):  # isolated
# # #             score -= 10
# # #     return score

# # # def _rook_queen_activity(board: chess.Board, colour: bool) -> int:
# # #     pawns_int    = int(board.pieces(chess.PAWN, chess.WHITE) |
# # #                        board.pieces(chess.PAWN, chess.BLACK))
# # #     occupied_own = int(board.occupied_co[colour])
# # #     bonus = 0
# # #     for sq in board.pieces(chess.ROOK, colour) | board.pieces(chess.QUEEN, colour):
# # #         file_mask = chess.BB_FILES[chess.square_file(sq)]
# # #         if not (file_mask & pawns_int):        # open file
# # #             bonus += 10
# # #         elif not (file_mask & occupied_own):   # semi-open
# # #             bonus += 5
# # #     return bonus

# # # def _king_safety(board: chess.Board, colour: bool) -> int:
# # #     k_sq = board.king(colour)
# # #     if k_sq is None:
# # #         return 0
# # #     file = chess.square_file(k_sq)
# # #     pawn_rank = 1 if colour else 6
# # #     missing = 0
# # #     for f in (file-1, file, file+1):
# # #         if 0 <= f <= 7:
# # #             sq = chess.square(f, pawn_rank)
# # #             if board.piece_type_at(sq) != chess.PAWN or board.color_at(sq) != colour:
# # #                 missing += 1
# # #     attackers = len(board.attackers(not colour, k_sq))
# # #     return -(15 * missing + 4 * attackers)

# # # # ──────────────────────────────────────────────────────────────
# # # # 5.  MAIN EVALUATION
# # # # ──────────────────────────────────────────────────────────────
# # # def evaluate(board: chess.Board) -> int:
# # #     mg_my = mg_opp = eg_my = eg_opp = 0
# # #     phase = START_PHASE

# # #     # material + PST
# # #     for sq, p in board.piece_map().items():
# # #         idx = _idx(sq, p.color)
# # #         val = WEIGHTS["material"][p.piece_type]
# # #         mg_val = val + PST_MG[p.piece_type][idx]
# # #         eg_val = val + PST_EG[p.piece_type][idx]
# # #         if p.color == board.turn:
# # #             mg_my += mg_val
# # #             eg_my += eg_val
# # #         else:
# # #             mg_opp += mg_val
# # #             eg_opp += eg_val
# # #         phase -= PHASE_UNIT[p.piece_type]

# # #     stm = board.turn
# # #     extras_my  = (_bishop_pair(board, stm)        +
# # #                   _passed_pawns(board, stm)       +
# # #                   _pawn_structure(board, stm)     +
# # #                   _rook_queen_activity(board, stm)+
# # #                   _king_safety(board, stm)        +
# # #                   _queen_safety(board, stm))      # ← NEW
# # #     extras_opp = (_bishop_pair(board, not stm)        +
# # #                   _passed_pawns(board, not stm)       +
# # #                   _pawn_structure(board, not stm)     +
# # #                   _rook_queen_activity(board, not stm)+
# # #                   _king_safety(board, not stm)        +
# # #                   _queen_safety(board, not stm))      # ← NEW

# # #     mg_score = mg_my - mg_opp + extras_my - extras_opp
# # #     eg_score = eg_my - eg_opp + extras_my - extras_opp

# # #     phase = max(0, phase)
# # #     score = (mg_score * phase + eg_score * (START_PHASE - phase)) // START_PHASE

# # #     # mobility (simple)
# # #     mob_my = board.legal_moves.count()
# # #     board.turn = not board.turn
# # #     mob_opp = board.legal_moves.count()
# # #     board.turn = not board.turn
# # #     score += 4 * (mob_my - mob_opp)

# # #     return score


# # """
# # engine/evaluation.py   –   Kestrel static evaluation
# # All scores are centipawns and returned from the side-to-move perspective
# # (positive = good for STM).
# # """

# # from __future__ import annotations
# # import chess
# # import functools

# # # ─────────────────────────────────────────────────────────────
# # # 1 ‑ Weights
# # # ─────────────────────────────────────────────────────────────
# # W = {
# #     # material
# #     "mat": {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
# #             chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0},

# #     # small extras
# #     "bishop_pair" : 30,
# #     "passed_rank" : [0, 5, 10, 20, 40, 60, 80, 100],
# #     "queen_danger": 800,

# #     # mobility (per legal destination)
# #     "mob": {chess.KNIGHT: 6, chess.BISHOP: 4,
# #             chess.ROOK  : 2, chess.QUEEN : 1},

# #     # king-ring attack weights
# #     "king_ring": {chess.PAWN  :  4,
# #                   chess.KNIGHT: 10,
# #                   chess.BISHOP: 12,
# #                   chess.ROOK  : 14,
# #                   chess.QUEEN : 24},

# #     # board control
# #     "centre_sq" : 4,
# #     "space_sq"  : 1,

# #     # development lag
# #     "undeveloped": -15,
# # }

# # # ─────────────────────────────────────────────────────────────
# # # 2 ‑ Piece-square tables (mid-game) – white view
# # #     End-game tables kept at 0 for now.
# # # ─────────────────────────────────────────────────────────────
# # PST_MG = {
# #     chess.PAWN: [
# #          0,  5,  5, -5, -5, 10, 50,  0,
# #          0, 10,-10,  0,  0, 10, 50,  0,
# #          0, 10,-10, 20, 25, 30, 50,  0,
# #          0,-20,  0,  0, 25, 30, 50,  0,
# #          0, 10,-10,  0, 25, 30, 50,  0,
# #          0, 10,-10,  0,  0, 10, 50,  0,
# #          0, 10,-10, -5, -5, 10, 50,  0,
# #          0,  5,  5, -5, -5, 10, 50,  0],
# #     chess.KNIGHT: [
# #        -50,-40,-30,-30,-30,-30,-40,-50,
# #        -40,-25, -5, -5, -5, -5,-25,-40,
# #        -30, -5, 10, 15, 15, 10, -5,-30,
# #        -30,  0, 15, 20, 20, 15,  0,-30,
# #        -30,  0, 15, 20, 20, 15,  0,-30,
# #        -30, -5, 10, 15, 15, 10, -5,-30,
# #        -40,-25, -5,  0,  0, -5,-25,-40,
# #        -50,-40,-30,-30,-30,-30,-40,-50],
# #     chess.BISHOP: [
# #        -20,-10,-10,-10,-10,-10,-10,-20,
# #        -10,  5,  0,  0,  0,  0,  5,-10,
# #        -10, 10, 10, 10, 10, 10, 10,-10,
# #        -10,  0, 10, 15, 15, 10,  0,-10,
# #        -10,  5,  5, 15, 15,  5,  5,-10,
# #        -10,  0,  5, 10, 10,  5,  0,-10,
# #        -10,  0,  0,  0,  0,  0,  0,-10,
# #        -20,-10,-10,-10,-10,-10,-10,-20],
# #     chess.ROOK  : [0]*64,
# #     chess.QUEEN : [0]*64,
# #     chess.KING  : [0]*64,
# # }

# # PST_EG = {pt: [0]*64 for pt in PST_MG}          # placeholder

# # # pad / truncate all PST lists to exactly 64 entries
# # for tbl in (PST_MG, PST_EG):
# #     for pt, arr in tbl.items():
# #         if len(arr) < 64:
# #             arr.extend([0] * (64 - len(arr)))
# #         elif len(arr) > 64:
# #             tbl[pt] = arr[:64]

# # # ─────────────────────────────────────────────────────────────
# # # 3 ‑ Phase & masks
# # # ─────────────────────────────────────────────────────────────
# # PHASE_UNIT  = {chess.PAWN:0, chess.KNIGHT:1, chess.BISHOP:1,
# #                chess.ROOK:2, chess.QUEEN:4, chess.KING:0}
# # START_PHASE = 24

# # CENTER_EXT = (chess.BB_SQUARES[chess.C4] | chess.BB_SQUARES[chess.D4] |
# #               chess.BB_SQUARES[chess.E4] | chess.BB_SQUARES[chess.F4] |
# #               chess.BB_SQUARES[chess.C5] | chess.BB_SQUARES[chess.D5] |
# #               chess.BB_SQUARES[chess.E5] | chess.BB_SQUARES[chess.F5])

# # WHITE_HALF = chess.BB_RANK_5 | chess.BB_RANK_6 | chess.BB_RANK_7 | chess.BB_RANK_8
# # BLACK_HALF = chess.BB_RANK_1 | chess.BB_RANK_2 | chess.BB_RANK_3 | chess.BB_RANK_4
# # BACK_RANK  = {chess.WHITE: chess.BB_RANK_1,
# #               chess.BLACK: chess.BB_RANK_8}

# # # ─────────────────────────────────────────────────────────────
# # # 4 ‑ helpers
# # # ─────────────────────────────────────────────────────────────
# # def _idx(sq: int, colour: bool) -> int:
# #     """PST index, mirrored for Black, clamped to [0-63]."""
# #     return max(0, min(63, sq if colour else chess.square_mirror(sq)))

# # @functools.lru_cache(maxsize=None)
# # def _ring_mask(sq: int) -> int:
# #     """8-square king ring."""
# #     f, r = chess.square_file(sq), chess.square_rank(sq)
# #     mask = 0
# #     for df in (-1, 0, 1):
# #         for dr in (-1, 0, 1):
# #             if df == dr == 0:
# #                 continue
# #             nf, nr = f + df, r + dr
# #             if 0 <= nf < 8 and 0 <= nr < 8:
# #                 mask |= chess.BB_SQUARES[chess.square(nf, nr)]
# #     return mask

# # _PVAL = {**W["mat"], chess.KING: 0}

# # # ─────────────────────────────────────────────────────────────
# # # 5 ‑ sub-scores
# # # ─────────────────────────────────────────────────────────────
# # def _bishop_pair(b: chess.Board, c: bool) -> int:
# #     return W["bishop_pair"] if len(b.pieces(chess.BISHOP, c)) == 2 else 0

# # def _queen_safety(b: chess.Board, c: bool) -> int:
# #     q = next(iter(b.pieces(chess.QUEEN, c)), None)
# #     if q is None:
# #         return 0
# #     opp = not c
# #     atk = b.attackers(opp, q)
# #     if not atk and not b.is_pinned(c, q):
# #         return 0

# #     def_bb = b.attackers(c, q)
# #     atk_val = sum(_PVAL[b.piece_type_at(s)] for s in atk)
# #     def_val = sum(_PVAL[b.piece_type_at(s)] for s in def_bb)
# #     balance = max(0, atk_val - def_val)

# #     # escape mobility (up to 5 safe squares × 60 cp)
# #     safe = 0
# #     for m in b.generate_legal_moves(from_mask=chess.BB_SQUARES[q]):
# #         b.push(m)
# #         if not b.attackers(opp, m.to_square):
# #             safe += 1
# #         b.pop()
# #         if safe == 5:
# #             break
# #     mobility = safe * 60
# #     pin_pen  = 200 if b.is_pinned(c, q) else 0
# #     penalty  = max(-200, min(900, balance - mobility + pin_pen))
# #     return -penalty

# # def _passed_pawns(b: chess.Board, c: bool) -> int:
# #     my  = int(b.pieces(chess.PAWN, c))
# #     opp = int(b.pieces(chess.PAWN, not c))
# #     bonus = 0
# #     bb = my
# #     while bb:
# #         sq = (bb & -bb).bit_length() - 1
# #         bb &= bb - 1
# #         f = chess.square_file(sq)
# #         front = chess.BB_FILES[f]
# #         front = front & ~((1 << (sq+1)) - 1) if c else front & ((1 << sq) - 1)
# #         side  = chess.BB_FILES[max(0, f-1)] | chess.BB_FILES[min(7, f+1)]
# #         if (front | (front & side)) & opp:
# #             continue
# #         rank = chess.square_rank(sq) if c else 7 - chess.square_rank(sq)
# #         bonus += W["passed_rank"][rank]
# #     return bonus

# # def _pawn_structure(b: chess.Board, c: bool) -> int:
# #     my = int(b.pieces(chess.PAWN, c))
# #     if not my:
# #         return 0
# #     score = 0
# #     for f in range(8):
# #         file_bb = my & chess.BB_FILES[f]
# #         cnt = file_bb.bit_count()
# #         if cnt > 1:
# #             score -= 8 * (cnt - 1)
# #         if cnt and not ((f and my & chess.BB_FILES[f-1]) or
# #                         (f < 7 and my & chess.BB_FILES[f+1])):
# #             score -= 10
# #     return score

# # def _rook_queen_activity(b: chess.Board, c: bool) -> int:
# #     pawn_mask = int(b.pieces(chess.PAWN, chess.WHITE) |
# #                     b.pieces(chess.PAWN, chess.BLACK))
# #     own_occ = int(b.occupied_co[c])
# #     bonus = 0
# #     for sq in b.pieces(chess.ROOK, c) | b.pieces(chess.QUEEN, c):
# #         mask = chess.BB_FILES[chess.square_file(sq)]
# #         bonus += 10 if not (mask & pawn_mask) else 5 if not (mask & own_occ) else 0
# #     return bonus

# # def _king_safety(b: chess.Board, c: bool) -> int:
# #     k = b.king(c)
# #     if k is None:
# #         return 0
# #     danger = 0
# #     for pt, val in W["king_ring"].items():
# #         attackers = b.attackers(not c, k) & b.pieces(pt, not c)
# #         danger += val * len(attackers)
# #     return -danger

# # def _mobility(b: chess.Board, c: bool) -> int:
# #     own_occ = b.occupied_co[c]
# #     score = 0
# #     for pt, w in W["mob"].items():
# #         for sq in b.pieces(pt, c):
# #             moves = len(b.attacks(sq) & ~own_occ)
# #             score += w * moves
# #     return score

# # def _centre(b: chess.Board, c: bool) -> int:
# #     attacks = 0
# #     for sq in chess.SquareSet(CENTER_EXT):
# #         attacks += len(b.attackers(c, sq))
# #     return W["centre_sq"] * attacks

# # def _space(b: chess.Board, c: bool) -> int:
# #     half = BLACK_HALF if c else WHITE_HALF
# #     ctrl = b.attacks_mask(c) & half
# #     return W["space_sq"] * ctrl.bit_count()

# # def _development(b: chess.Board, c: bool) -> int:
# #     if len(b.move_stack) < 20:
# #         return 0
# #     minors = b.pieces(chess.KNIGHT, c) | b.pieces(chess.BISHOP, c)
# #     return W["undeveloped"] * len(minors & BACK_RANK[c])

# # # ─────────────────────────────────────────────────────────────
# # # 6 ‑ main evaluate
# # # ─────────────────────────────────────────────────────────────
# # def evaluate(board: chess.Board) -> int:
# #     mg_my = mg_opp = eg_my = eg_opp = 0
# #     phase = START_PHASE

# #     for sq, p in board.piece_map().items():
# #         idx = _idx(sq, p.color)
# #         val = W["mat"][p.piece_type]
# #         mg_val = val + PST_MG[p.piece_type][idx]
# #         eg_val = val + PST_EG[p.piece_type][idx]
# #         if p.color == board.turn:
# #             mg_my += mg_val
# #             eg_my += eg_val
# #         else:
# #             mg_opp += mg_val
# #             eg_opp += eg_val
# #         phase -= PHASE_UNIT[p.piece_type]

# #     stm = board.turn
# #     extras_my  = (_bishop_pair(board, stm)      + _passed_pawns(board, stm) +
# #                   _pawn_structure(board, stm)   + _rook_queen_activity(board, stm) +
# #                   _king_safety(board, stm)      + _queen_safety(board, stm) +
# #                   _mobility(board, stm)         + _centre(board, stm) +
# #                   _space(board, stm)            + _development(board, stm))

# #     extras_opp = (_bishop_pair(board, not stm)  + _passed_pawns(board, not stm) +
# #                   _pawn_structure(board, not stm) + _rook_queen_activity(board, not stm) +
# #                   _king_safety(board, not stm)    + _queen_safety(board, not stm) +
# #                   _mobility(board, not stm)       + _centre(board, not stm) +
# #                   _space(board, not stm)          + _development(board, not stm))

# #     mg_score = mg_my - mg_opp + extras_my - extras_opp
# #     eg_score = eg_my - eg_opp + extras_my - extras_opp

# #     phase = max(0, phase)
# #     return (mg_score * phase + eg_score * (START_PHASE - phase)) // START_PHASE



# """
# engine/evaluation.py  •  fast, tapered mid/late evaluation
# All numbers in centipawns and returned from the side-to-move POV.
# """

# from __future__ import annotations
# import chess, functools

# W = {
#     "mat": {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 335,
#             chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0},

#     "bishop_pair": 40,
#     "tempo": 15,                   # bonus for side to move

#     "passed":  [0, 5, 10, 25, 45, 70, 110, 180],  # 8 ranks
#     "isolated": 12,
#     "doubled": 8,

#     # mobility bonus per legal destination
#     "mob": {chess.KNIGHT: 4, chess.BISHOP: 4,
#             chess.ROOK: 2, chess.QUEEN: 1},

#     # PSTs (mid-game) — shortened for space; feel free to refine
#     "pst": {
#         chess.PAWN:   [ 0,  5,  5, -5, -5, 10, 50,  0] * 8,
#         chess.KNIGHT: [-30, -20, -10, -10, -10, -10, -20, -30] * 8,
#         chess.BISHOP: [-20, -10, -10, -10, -10, -10, -10, -20] * 8,
#         chess.ROOK:   [0] * 64,
#         chess.QUEEN:  [0] * 64,
#         chess.KING:   [0] * 64
#     }
# }

# # end-game tables kept at zero
# PST_EG = {pt: [0] * 64 for pt in W["pst"]}
# PHASE_UNIT = {chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 1,
#               chess.ROOK: 2, chess.QUEEN: 4, chess.KING: 0}
# START_PHASE = 24


# def _idx(sq: int, color: bool) -> int:
#     return sq if color else chess.square_mirror(sq)


# # ───────────────────── pawn structure helpers ──────────────────
# @functools.lru_cache(maxsize=None)
# def _file_mask(file: int) -> int:
#     return chess.BB_FILES[file]


# def _pawn_structure(board: chess.Board, color: bool) -> int:
#     pawns = int(board.pieces(chess.PAWN, color))
#     if not pawns:
#         return 0
#     score = 0
#     for f in range(8):
#         mask = pawns & _file_mask(f)
#         cnt = mask.bit_count()
#         if cnt >= 2:
#             score -= W["doubled"] * (cnt - 1)
#         if cnt and not ((f and pawns & _file_mask(f - 1)) or
#                         (f < 7 and pawns & _file_mask(f + 1))):
#             score -= W["isolated"]
#     # passed pawns
#     opp_pawns = int(board.pieces(chess.PAWN, not color))
#     bb = pawns
#     while bb:
#         sq = (bb & -bb).bit_length() - 1
#         bb &= bb - 1
#         f = chess.square_file(sq)
#         front = _file_mask(f)
#         front = front & ~((1 << (sq + 1)) - 1) if color else front & ((1 << sq) - 1)
#         side = _file_mask(max(0, f - 1)) | _file_mask(min(7, f + 1))
#         if (front | (front & side)) & opp_pawns:
#             continue
#         rank = chess.square_rank(sq) if color else 7 - chess.square_rank(sq)
#         score += W["passed"][rank]
#     return score


# def _mobility(board: chess.Board, color: bool) -> int:
#     own_occ = board.occupied_co[color]
#     sc = 0
#     for pt, w in W["mob"].items():
#         for sq in board.pieces(pt, color):
#             sc += w * len(board.attacks(sq) & ~own_occ)
#     return sc


# # ───────────────────────── main eval ───────────────────────────
# def evaluate(board: chess.Board) -> int:
#     mg_my = mg_opp = eg_my = eg_opp = 0
#     phase = START_PHASE

#     for sq, p in board.piece_map().items():
#         idx = _idx(sq, p.color)
#         val = W["mat"][p.piece_type]
#         mg_val = val + W["pst"][p.piece_type][idx]
#         eg_val = val + PST_EG[p.piece_type][idx]
#         if p.color == board.turn:
#             mg_my += mg_val
#             eg_my += eg_val
#         else:
#             mg_opp += mg_val
#             eg_opp += eg_val
#         phase -= PHASE_UNIT[p.piece_type]

#     stm = board.turn
#     extras_my = (_pawn_structure(board, stm) +
#                  _mobility(board, stm) +
#                  (W["bishop_pair"] if len(board.pieces(chess.BISHOP, stm)) == 2 else 0))
#     extras_opp = (_pawn_structure(board, not stm) +
#                   _mobility(board, not stm) +
#                   (W["bishop_pair"] if len(board.pieces(chess.BISHOP, not stm)) == 2 else 0))

#     mg_score = mg_my - mg_opp + extras_my - extras_opp
#     eg_score = eg_my - eg_opp + extras_my - extras_opp

#     phase = max(0, phase)
#     score = (mg_score * phase + eg_score * (START_PHASE - phase)) // START_PHASE

#     return score + W["tempo"]          # tempo bonus


"""
engine/evaluation.py  •  tapered mid/late evaluation
Now includes:
    – king-shield bonus / penalty
    – penalty for hanging (undefended & attacked) pieces
All values in centipawns, evaluated from the side-to-move perspective.
"""
from __future__ import annotations
import chess, functools

# ───────────── weights ─────────────
W = {
    # material
    "mat": {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 335,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0},

    # misc bonuses / penalties
    "bishop_pair": 40,
    "tempo": 15,

    # king safety: bonus (negative list → less shield ⇒ bigger penalty)
    "king_shield": [0, -10, -20, -35, -50],   # index = rank distance from own back-rank
    "hanging": -30,                           # per undefended, attacked piece

    # pawn structure
    "passed":  [0, 5, 10, 25, 45, 70, 110, 180],
    "isolated": 12,
    "doubled": 8,

    # mobility per legal destination
    "mob": {chess.KNIGHT: 4, chess.BISHOP: 4,
            chess.ROOK: 2, chess.QUEEN: 1},

    # piece-square tables (mid-game) – shortened for brevity
    "pst": {
        chess.PAWN:   [ 0,  5,  5, -5, -5, 10, 50,  0] * 8,
        chess.KNIGHT: [-30, -20, -10, -10, -10, -10, -20, -30] * 8,
        chess.BISHOP: [-20, -10, -10, -10, -10, -10, -10, -20] * 8,
        chess.ROOK:   [0] * 64,
        chess.QUEEN:  [0] * 64,
        chess.KING:   [0] * 64
    }
}

# end-game PST kept zero
PST_EG = {pt: [0] * 64 for pt in W["pst"]}

# phase weights
PHASE_UNIT   = {chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 1,
                chess.ROOK: 2, chess.QUEEN: 4, chess.KING: 0}
START_PHASE  = 24


def _idx(sq: int, color: bool) -> int:
    """Return table index, mirrored for Black."""
    return sq if color else chess.square_mirror(sq)


# ───────── pawn-structure helpers ─────────
@functools.lru_cache(maxsize=None)
def _file_mask(file: int) -> int:
    return chess.BB_FILES[file]


def _pawn_structure(board: chess.Board, color: bool) -> int:
    pawns = int(board.pieces(chess.PAWN, color))
    if not pawns:
        return 0
    score = 0
    for f in range(8):
        mask = pawns & _file_mask(f)
        cnt  = mask.bit_count()
        if cnt >= 2:
            score -= W["doubled"] * (cnt - 1)
        if cnt and not ((f and pawns & _file_mask(f - 1)) or
                        (f < 7 and pawns & _file_mask(f + 1))):
            score -= W["isolated"]
    # passed pawns
    opp_pawns = int(board.pieces(chess.PAWN, not color))
    bb = pawns
    while bb:
        sq = (bb & -bb).bit_length() - 1
        bb &= bb - 1
        f = chess.square_file(sq)
        front = _file_mask(f)
        front = front & ~((1 << (sq + 1)) - 1) if color else front & ((1 << sq) - 1)
        side  = _file_mask(max(0, f - 1)) | _file_mask(min(7, f + 1))
        if (front | (front & side)) & opp_pawns:
            continue
        rank = chess.square_rank(sq) if color else 7 - chess.square_rank(sq)
        score += W["passed"][rank]
    return score


def _mobility(board: chess.Board, color: bool) -> int:
    own_occ = board.occupied_co[color]
    sc = 0
    for pt, wt in W["mob"].items():
        for sq in board.pieces(pt, color):
            sc += wt * len(board.attacks(sq) & ~own_occ)
    return sc


# ───────── new tactical extras ─────────
def _king_safety(board: chess.Board, color: bool) -> int:
    k_sq = board.king(color)
    if k_sq is None:
        return 0
    file = chess.square_file(k_sq)
    rank_dist = chess.square_rank(k_sq) if color else 7 - chess.square_rank(k_sq)
    shield = 0
    for f in (file - 1, file, file + 1):
        if 0 <= f <= 7:
            sq = chess.square(f, 1 if color else 6)
            if board.piece_type_at(sq) == chess.PAWN and board.color_at(sq) == color:
                shield += 1
    return W["king_shield"][min(rank_dist, 4)] * (3 - shield)


def _hanging(board: chess.Board, color: bool) -> int:
    sc = 0
    for sq, pc in board.piece_map().items():
        if pc.color != color:
            continue
        if not board.is_attacked_by(not color, sq):
            continue                     # not under fire
        if board.is_attacked_by(color, sq):
            continue                     # defended
        sc += W["hanging"]
    return sc


# ───────────── main evaluation ──────────
def evaluate(board: chess.Board) -> int:
    mg_my = mg_opp = eg_my = eg_opp = 0
    phase = START_PHASE

    for sq, p in board.piece_map().items():
        idx = _idx(sq, p.color)
        val = W["mat"][p.piece_type]

        mg_val = val + W["pst"][p.piece_type][idx]
        eg_val = val + PST_EG[p.piece_type][idx]

        if p.color == board.turn:
            mg_my += mg_val
            eg_my += eg_val
        else:
            mg_opp += mg_val
            eg_opp += eg_val

        phase -= PHASE_UNIT[p.piece_type]

    stm = board.turn
    extras_my = (_pawn_structure(board, stm) +
                 _mobility(board, stm) +
                 _king_safety(board, stm) +
                 _hanging(board, not stm) +
                 (W["bishop_pair"] if len(board.pieces(chess.BISHOP, stm)) == 2 else 0))

    extras_opp = (_pawn_structure(board, not stm) +
                  _mobility(board, not stm) +
                  _king_safety(board, not stm) +
                  _hanging(board, stm) +
                  (W["bishop_pair"] if len(board.pieces(chess.BISHOP, not stm)) == 2 else 0))

    mg_score = mg_my - mg_opp + extras_my - extras_opp
    eg_score = eg_my - eg_opp + extras_my - extras_opp

    phase = max(0, phase)
    score = (mg_score * phase + eg_score * (START_PHASE - phase)) // START_PHASE

    return score + W["tempo"]          # tempo bonus
