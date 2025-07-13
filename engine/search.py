# # # import time, random, chess
# # # from .evaluation import evaluate
# # # from .transposition import zobrist_hash, probe, store, EXACT, LOWER, UPPER

# # # INF, MAX_PLY = 10_000, 64
# # # KILLERS = [[None, None] for _ in range(MAX_PLY)]
# # # HISTORY = {}

# # # # promotion priority: Q > R > B > N
# # # PROMO_ORDER = {chess.QUEEN: 4, chess.ROOK: 3,
# # #                chess.BISHOP: 2, chess.KNIGHT: 1}

# # # def _grow_killers(ply: int):
# # #     if ply >= len(KILLERS):
# # #         KILLERS.extend([[None, None]] * (ply - len(KILLERS) + 16))

# # # # ───────────────────────── root driver ─────────────────────────
# # # def find_best_move(board: chess.Board, time_limit: float = 2.0):
# # #     best, depth, score, asp = None, 1, 0, 30
# # #     t0 = time.time()
# # #     while True:
# # #         a, b = score - asp, score + asp
# # #         while True:
# # #             try:
# # #                 score, move = _alphabeta(board, depth, a, b, 0, t0, time_limit)
# # #             except TimeoutError:
# # #                 return best or random.choice(list(board.legal_moves))
# # #             if score <= a:  a -= asp;  continue
# # #             if score >= b:  b += asp;  continue
# # #             break
# # #         if move: best = move
# # #         depth += 1
# # #         if time.time() - t0 > time_limit or depth > 512:
# # #             return best

# # # # ───────────────────── alpha-beta core ────────────────────────
# # # def _alphabeta(board: chess.Board, depth: int, alpha: int, beta: int,
# # #                ply: int, t0: float, tl: float):
# # #     _grow_killers(ply)

# # #     # base cases
# # #     if depth <= 0:
# # #         return _quiescence(board, alpha, beta), None
# # #     if board.is_checkmate():
# # #         return -INF + ply, None
# # #     if board.is_stalemate() or board.is_insufficient_material():
# # #         return 0, None
# # #     if time.time() - t0 > tl:
# # #         raise TimeoutError

# # #     # TT probe
# # #     h = zobrist_hash(board)
# # #     tt = probe(h)
# # #     if tt and tt.depth >= depth:
# # #         if tt.flag == EXACT:
# # #             return tt.score, tt.move
# # #         if tt.flag == LOWER and tt.score > alpha:
# # #             alpha = tt.score
# # #         elif tt.flag == UPPER and tt.score < beta:
# # #             beta = tt.score
# # #         if alpha >= beta:
# # #             return tt.score, tt.move

# # #     # null-move pruning (safe)
# # #     if depth >= 4 and not board.is_check():
# # #         if any(board.pieces(pt, board.turn) for pt in
# # #                (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)):
# # #             board.push(chess.Move.null())
# # #             try:
# # #                 v, _ = _alphabeta(board, depth-3, -beta, -(beta-1),
# # #                                   ply+1, t0, tl)
# # #                 v = -v
# # #             except TimeoutError:
# # #                 board.pop();  raise
# # #             board.pop()
# # #             if v >= beta:
# # #                 store(h, depth, beta, LOWER, None)
# # #                 return beta, None

# # #     best_move = None
# # #     moves = list(board.legal_moves)
# # #     # hash move first
# # #     if tt and tt.move in moves:
# # #         moves.remove(tt.move); moves.insert(0, tt.move)
# # #     moves.sort(key=lambda m: _score_move(board, m, ply), reverse=True)

# # #     for idx, mv in enumerate(moves):
# # #         new_depth = depth - 1
# # #         # never reduce promotions
# # #         if (idx >= 6 and depth >= 4 and
# # #             not board.is_check() and
# # #             not board.is_capture(mv) and mv.promotion is None):
# # #             new_depth -= 1
# # #         if new_depth < 0: new_depth = 0

# # #         board.push(mv)
# # #         try:
# # #             val, _ = _alphabeta(board, new_depth, -beta, -alpha,
# # #                                 ply+1, t0, tl)
# # #             val = -val
# # #         except TimeoutError:
# # #             board.pop(); raise
# # #         board.pop()

# # #         if val >= beta:
# # #             if not board.is_capture(mv) and mv.promotion is None:
# # #                 if mv not in KILLERS[ply]:
# # #                     KILLERS[ply][1] = KILLERS[ply][0]
# # #                     KILLERS[ply][0] = mv
# # #                 HISTORY[mv] = HISTORY.get(mv, 0) + depth*depth
# # #             store(h, depth, beta, LOWER, mv)
# # #             return beta, mv
# # #         if val > alpha:
# # #             alpha, best_move = val, mv

# # #     store(h, depth, alpha, EXACT if best_move else UPPER, best_move)
# # #     return alpha, best_move

# # # # ───────────────────── quiescence ────────────────────────────
# # # def _quiescence(board: chess.Board, alpha: int, beta: int):
# # #     stand = evaluate(board)
# # #     if stand >= beta:
# # #         return beta
# # #     if alpha < stand:
# # #         alpha = stand

# # #     for mv in board.legal_moves:
# # #         if not board.is_capture(mv) and mv.promotion is None:
# # #             continue
# # #         board.push(mv)
# # #         score = -_quiescence(board, -beta, -alpha)
# # #         board.pop()
# # #         if score >= beta:
# # #             return beta
# # #         if score > alpha:
# # #             alpha = score
# # #     return alpha

# # # # ─────────────────── move ordering ───────────────────────────
# # # def _score_move(board: chess.Board, mv: chess.Move, ply: int) -> int:
# # #     # promotions: highest priority
# # #     if mv.promotion is not None:
# # #         return 15_000 + 1_000 * PROMO_ORDER[mv.promotion]

# # #     # captures – MVV/LVA
# # #     if board.is_capture(mv):
# # #         vict = board.piece_at(mv.to_square)
# # #         if vict is None and board.is_en_passant(mv):
# # #             ep = mv.to_square + (-8 if board.turn else 8)
# # #             vict = board.piece_at(ep)
# # #         v = vict.piece_type if vict else 0
# # #         a = board.piece_at(mv.from_square).piece_type
# # #         return 10_000 + 10*v - a

# # #     # killer moves
# # #     if ply < len(KILLERS) and mv in KILLERS[ply]:
# # #         return 9_000

# # #     # history
# # #     return HISTORY.get(mv, 0)

# # import time
# # import random
# # import chess

# # from .evaluation import evaluate
# # from .transposition import (
# #     zobrist_hash, probe, store,
# #     EXACT, LOWER, UPPER,
# # )

# # INF        = 10_000
# # MAX_PLY    = 64                 # starting size – auto-grows
# # KILLERS    = [[None, None] for _ in range(MAX_PLY)]
# # HISTORY    = {}

# # # promotion priority: Q > R > B > N
# # PROMO_ORDER = {chess.QUEEN: 4, chess.ROOK: 3,
# #                chess.BISHOP: 2, chess.KNIGHT: 1}


# # # ───────────────────────── helpers ──────────────────────────
# # def _grow_killers(ply: int) -> None:
# #     if ply >= len(KILLERS):
# #         KILLERS.extend([[None, None]] * (ply - len(KILLERS) + 16))


# # # ─────────────────────── root driver ───────────────────────
# # def find_best_move(board: chess.Board, time_limit: float = 2.0):
# #     best_move, depth, score, asp = None, 1, 0, 30
# #     t0 = time.time()

# #     while True:
# #         alpha, beta = score - asp, score + asp
# #         while True:
# #             try:
# #                 score, move = _alphabeta(board, depth, alpha, beta,
# #                                          0, t0, time_limit)
# #             except TimeoutError:
# #                 return best_move or random.choice(list(board.legal_moves))

# #             if score <= alpha:  alpha -= asp;  continue     # fail-low
# #             if score >= beta:   beta  += asp;  continue     # fail-high
# #             break

# #         if move:
# #             best_move = move
# #         depth += 1

# #         if time.time() - t0 > time_limit or depth > 512:
# #             return best_move


# # # ─────────────────── alpha-beta core ───────────────────────
# # def _alphabeta(board: chess.Board, depth: int, alpha: int, beta: int,
# #                ply: int, t0: float, tl: float):
# #     _grow_killers(ply)

# #     # base cases
# #     if depth <= 0:
# #         return _quiescence(board, alpha, beta), None
# #     if board.is_checkmate():
# #         return -INF + ply, None
# #     if board.is_stalemate() or board.is_insufficient_material():
# #         return 0, None
# #     if time.time() - t0 > tl:
# #         raise TimeoutError

# #     # transposition-table probe
# #     key = zobrist_hash(board)
# #     tt  = probe(key)
# #     if tt and tt.depth >= depth:
# #         if tt.flag == EXACT:
# #             return tt.score, tt.move
# #         if tt.flag == LOWER and tt.score > alpha:
# #             alpha = tt.score
# #         elif tt.flag == UPPER and tt.score < beta:
# #             beta = tt.score
# #         if alpha >= beta:
# #             return tt.score, tt.move

# #     # safe null-move pruning
# #     if (depth >= 4 and not board.is_check() and
# #         any(board.pieces(pt, board.turn)
# #             for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN))):
# #         board.push(chess.Move.null())
# #         try:
# #             v, _ = _alphabeta(board, depth - 3, -beta, -(beta - 1),
# #                               ply + 1, t0, tl)
# #             v = -v
# #         except TimeoutError:
# #             board.pop();  raise
# #         board.pop()
# #         if v >= beta:
# #             store(key, depth, beta, LOWER, None)
# #             return beta, None

# #     # move list & ordering
# #     moves = list(board.legal_moves)
# #     if tt and tt.move in moves:
# #         moves.remove(tt.move)
# #         moves.insert(0, tt.move)
# #     moves.sort(key=lambda m: _score_move(board, m, ply), reverse=True)

# #     best_move = None
# #     for idx, mv in enumerate(moves):
# #         new_depth = depth - 1

# #         # late-move reduction – skip for captures, checks, promotions
# #         if (idx >= 6 and depth >= 4 and
# #             not board.is_check() and
# #             not board.is_capture(mv) and
# #             mv.promotion is None and
# #             not board.gives_check(mv)):
# #             new_depth -= 1
# #         if new_depth < 0:
# #             new_depth = 0

# #         board.push(mv)
# #         try:
# #             val, _ = _alphabeta(board, new_depth, -beta, -alpha,
# #                                 ply + 1, t0, tl)
# #             val = -val
# #         except TimeoutError:
# #             board.pop();  raise
# #         board.pop()

# #         if val >= beta:
# #             if (not board.is_capture(mv) and mv.promotion is None
# #                     and mv not in KILLERS[ply]):
# #                 KILLERS[ply][1] = KILLERS[ply][0]
# #                 KILLERS[ply][0] = mv
# #             HISTORY[mv] = HISTORY.get(mv, 0) + depth * depth
# #             store(key, depth, beta, LOWER, mv)
# #             return beta, mv

# #         if val > alpha:
# #             alpha, best_move = val, mv

# #     store(key, depth, alpha,
# #           EXACT if best_move else UPPER, best_move)
# #     return alpha, best_move


# # # ──────────────────── quiescence ────────────────────────────
# # def _quiescence(board: chess.Board, alpha: int, beta: int):
# #     stand = evaluate(board)
# #     if stand >= beta:
# #         return beta
# #     if alpha < stand:
# #         alpha = stand

# #     for mv in board.legal_moves:
# #         if (not board.is_capture(mv) and
# #             mv.promotion is None and
# #             not board.gives_check(mv)):
# #             continue
# #         board.push(mv)
# #         score = -_quiescence(board, -beta, -alpha)
# #         board.pop()

# #         if score >= beta:
# #             return beta
# #         if score > alpha:
# #             alpha = score
# #     return alpha


# # # ───────────────── move ordering ────────────────────────────
# # def _score_move(board: chess.Board, mv: chess.Move, ply: int) -> int:
# #     # 1. promotions – top priority
# #     if mv.promotion is not None:
# #         return 15_000 + 1_000 * PROMO_ORDER[mv.promotion]

# #     # 2. captures – MVV/LVA
# #     if board.is_capture(mv):
# #         victim = board.piece_at(mv.to_square)
# #         if victim is None and board.is_en_passant(mv):
# #             ep_sq = mv.to_square + (-8 if board.turn else 8)
# #             victim = board.piece_at(ep_sq)
# #         v_val   = victim.piece_type if victim else 0
# #         a_val   = board.piece_at(mv.from_square).piece_type
# #         return 10_000 + 10 * v_val - a_val

# #     # 3. killer moves
# #     if ply < len(KILLERS) and mv in KILLERS[ply]:
# #         return 9_000

# #     # 4. quiet checks (demoted but still above history)
# #     if board.gives_check(mv):
# #         return 2_500

# #     # 5. history
# #     return HISTORY.get(mv, 0)


# """
# engine/search.py  •  iterative deepening PVS with SEE, LMR, killers & history
# """

# from __future__ import annotations
# import time, random, chess

# from .evaluation import evaluate
# from .see import see
# from .transposition import zobrist_hash, probe, store, EXACT, LOWER, UPPER

# INF = 10_000
# MAX_PLY = 128
# KILLERS = [[None, None] for _ in range(MAX_PLY)]
# HISTORY: dict[chess.Move, int] = {}

# # promotion priority
# PROMO_ORDER = {chess.QUEEN: 4, chess.ROOK: 3, chess.BISHOP: 2, chess.KNIGHT: 1}


# def _grow(ply: int):
#     if ply >= len(KILLERS):
#         KILLERS.extend([[None, None]] * (ply - len(KILLERS) + 32))


# # ────────────────────── root driver ────────────────────────────
# def find_best_move(board: chess.Board, time_limit: float = 2.0) -> chess.Move:
#     best, depth, score = None, 1, 0
#     t0 = time.perf_counter()
#     aspiration = 30

#     while True:
#         alpha, beta = score - aspiration, score + aspiration
#         while True:
#             try:
#                 score, pv_move = _pvs(board, depth, alpha, beta, 0, t0, time_limit)
#             except TimeoutError:
#                 return best or random.choice(list(board.legal_moves))
#             if score <= alpha:
#                 alpha -= aspiration
#                 aspiration *= 2
#                 continue      # fail-low
#             if score >= beta:
#                 beta += aspiration
#                 aspiration *= 2
#                 continue      # fail-high
#             break

#         if pv_move:
#             best = pv_move
#         depth += 1
#         if time.perf_counter() - t0 > time_limit or depth > 64:
#             return best


# # ───────────────── principal-variation search ──────────────────
# def _pvs(board: chess.Board, depth: int, alpha: int, beta: int,
#          ply: int, t0: float, tl: float) -> tuple[int, chess.Move | None]:
#     _grow(ply)

#     # basic terminal checks
#     if depth <= 0:
#         return _quiescence(board, alpha, beta), None
#     if board.is_checkmate():
#         return -INF + ply, None
#     if board.is_stalemate() or board.can_claim_draw():
#         return 0, None
#     if time.perf_counter() - t0 > tl:
#         raise TimeoutError

#     key = zobrist_hash(board)
#     tt = probe(key)
#     if tt and tt.depth >= depth:
#         if tt.flag == EXACT:
#             return tt.score, tt.move
#         if tt.flag == LOWER and tt.score > alpha:
#             alpha = tt.score
#         elif tt.flag == UPPER and tt.score < beta:
#             beta = tt.score
#         if alpha >= beta:
#             return tt.score, tt.move

#     # null-move pruning (safe)
#     if depth >= 3 and not board.is_check() and \
#        any(board.pieces(pt, board.turn) for pt in (chess.ROOK, chess.QUEEN,
#                                                    chess.BISHOP, chess.KNIGHT)):
#         board.push(chess.Move.null())
#         try:
#             v, _ = _pvs(board, depth - 1 - 2, -beta, -(beta - 1),
#                         ply + 1, t0, tl)
#             v = -v
#         except TimeoutError:
#             board.pop(); raise
#         board.pop()
#         if v >= beta:
#             store(key, depth, beta, LOWER, None)
#             return beta, None

#     best_move = None
#     moves = _ordered_moves(board, ply, tt)
#     first = True

#     for idx, mv in enumerate(moves):
#         red = 0
#         if not first and depth >= 3 and idx >= 6 and \
#            not board.is_capture(mv) and mv.promotion is None and \
#            not board.gives_check(mv):
#             red = 1                                    # LMR

#         board.push(mv)
#         try:
#             if first:
#                 val, _ = _pvs(board, depth - 1, -beta, -alpha,
#                                ply + 1, t0, tl)
#                 val = -val
#             else:
#                 # PVS search window
#                 val, _ = _pvs(board, depth - 1 - red, -alpha - 1, -alpha,
#                                ply + 1, t0, tl)
#                 val = -val
#                 if alpha < val < beta:                 # re-search
#                     val, _ = _pvs(board, depth - 1, -beta, -alpha,
#                                    ply + 1, t0, tl)
#                     val = -val
#         except TimeoutError:
#             board.pop(); raise
#         board.pop()

#         if val >= beta:
#             _record_killer(mv, ply, depth)
#             store(key, depth, beta, LOWER, mv)
#             return beta, mv
#         if val > alpha:
#             alpha, best_move = val, mv
#         first = False

#     store(key, depth, alpha, EXACT if best_move else UPPER, best_move)
#     return alpha, best_move


# # ───────────────────── quiescence with SEE ─────────────────────
# def _quiescence(board: chess.Board, alpha: int, beta: int) -> int:
#     stand = evaluate(board)
#     if stand >= beta:
#         return beta
#     if alpha < stand:
#         alpha = stand

#     for mv in board.legal_moves:
#         if not board.is_capture(mv) and mv.promotion is None and \
#            not board.gives_check(mv):
#             continue
#         if see(board, mv, threshold=50) <= 0:
#             continue                                   # bad capture

#         board.push(mv)
#         score = -_quiescence(board, -beta, -alpha)
#         board.pop()

#         if score >= beta:
#             return beta
#         if score > alpha:
#             alpha = score
#     return alpha


# # ───────────────────── move ordering helpers ──────────────────
# def _record_killer(mv: chess.Move, ply: int, depth: int):
#     if mv not in KILLERS[ply]:
#         KILLERS[ply][1] = KILLERS[ply][0]
#         KILLERS[ply][0] = mv
#     HISTORY[mv] = HISTORY.get(mv, 0) + depth * depth


# def _ordered_moves(board: chess.Board, ply: int, tt_hit) -> list[chess.Move]:
#     moves = list(board.legal_moves)

#     if tt_hit and tt_hit.move in moves:
#         moves.remove(tt_hit.move)
#         moves.insert(0, tt_hit.move)

#     moves.sort(key=lambda m: _score(board, m, ply), reverse=True)
#     return moves


# def _score(board: chess.Board, mv: chess.Move, ply: int) -> int:
#     # 1. promotions
#     if mv.promotion:
#         return 15_000 + 1_000 * PROMO_ORDER[mv.promotion]
#     # 2. captures (MVV/LVA) + SEE bonus
#     if board.is_capture(mv):
#         victim = board.piece_at(mv.to_square)
#         if victim is None and board.is_en_passant(mv):
#             ep = mv.to_square + (-8 if board.turn else 8)
#             victim = board.piece_at(ep)
#         v = victim.piece_type if victim else 0
#         a = board.piece_at(mv.from_square).piece_type
#         see_bonus = see(board, mv)
#         return 10_000 + 10 * v - a + see_bonus
#     # 3. killer moves
#     if mv in KILLERS[ply]:
#         return 9_000
#     # 4. checks
#     if board.gives_check(mv):
#         return 3_000
#     # 5. history
#     return HISTORY.get(mv, 0)


"""
engine/search.py  •  iterative deepening PVS with:
    – static-exchange evaluation (SEE)
    – history + killer heuristics
    – late-move reductions (LMR) that *never* reduce checking moves
    – selective depth extensions:
        • side-to-move is in check
        • current move gives check *and* SEE judges the follow-up favourable
"""

from __future__ import annotations
import time, random, chess

from .evaluation   import evaluate
from .see          import see
from .transposition import zobrist_hash, probe, store, EXACT, LOWER, UPPER

INF       = 10_000
MAX_PLY   = 128
CHECK_EXT = 1          # +1 ply when side to move is in check
FORCE_EXT = 1          # +1 ply after a checking move that wins material

KILLERS:  list[list[chess.Move | None]] = [[None, None] for _ in range(MAX_PLY)]
HISTORY:  dict[chess.Move, int] = {}

PROMO_ORDER = {chess.QUEEN: 4, chess.ROOK: 3, chess.BISHOP: 2, chess.KNIGHT: 1}


def _grow(ply: int) -> None:
    if ply >= len(KILLERS):
        KILLERS.extend([[None, None]] * (ply - len(KILLERS) + 32))


# ───────────────────── root driver ─────────────────────────────
def find_best_move(board: chess.Board, time_limit: float = 2.0) -> chess.Move:
    best, depth, score = None, 1, 0
    t0 = time.perf_counter()
    aspiration = 30

    while True:
        alpha, beta = score - aspiration, score + aspiration
        while True:
            try:
                score, pv_move = _pvs(board, depth, alpha, beta, 0, t0, time_limit)
            except TimeoutError:
                return best or random.choice(list(board.legal_moves))
            if score <= alpha:  alpha -= aspiration; aspiration *= 2; continue
            if score >= beta:   beta += aspiration; aspiration *= 2; continue
            break

        if pv_move:
            best = pv_move
        depth += 1
        if time.perf_counter() - t0 > time_limit or depth > 64:
            return best


# ───────────── principal-variation search ─────────────────────
def _pvs(board: chess.Board, depth: int, alpha: int, beta: int,
         ply: int, t0: float, tl: float) -> tuple[int, chess.Move | None]:

    _grow(ply)

    # selective extension: side to move is in check
    if board.is_check():
        depth += CHECK_EXT

    if depth <= 0:
        return _quiescence(board, alpha, beta), None
    if board.is_checkmate():
        return -INF + ply, None
    if board.is_stalemate() or board.can_claim_draw():
        return 0, None
    if time.perf_counter() - t0 > tl:
        raise TimeoutError

    key = zobrist_hash(board)
    tt  = probe(key)
    if tt and tt.depth >= depth:
        if tt.flag == EXACT:
            return tt.score, tt.move
        if tt.flag == LOWER and tt.score > alpha:
            alpha = tt.score
        elif tt.flag == UPPER and tt.score < beta:
            beta = tt.score
        if alpha >= beta:
            return tt.score, tt.move

    # null-move pruning (safe)
    if depth >= 3 and not board.is_check() and \
       any(board.pieces(pt, board.turn) for pt in (chess.ROOK, chess.QUEEN,
                                                   chess.BISHOP, chess.KNIGHT)):
        board.push(chess.Move.null())
        try:
            v, _ = _pvs(board, depth - 1 - 2, -beta, -(beta - 1),
                        ply + 1, t0, tl)
            v = -v
        except TimeoutError:
            board.pop(); raise
        board.pop()
        if v >= beta:
            store(key, depth, beta, LOWER, None)
            return beta, None

    best_move = None
    moves     = _ordered_moves(board, ply, tt)
    first     = True

    for idx, mv in enumerate(moves):
        gives_chk = board.gives_check(mv)

        # late-move reduction — *never* reduce checking moves
        red = 0
        if not first and depth >= 3 and idx >= 6 and \
           not board.is_capture(mv) and mv.promotion is None and \
           not gives_chk:
            red = 1

        board.push(mv)
        try:
            forcing = gives_chk and see(board, mv, threshold=50) > 0
            child_d = depth - 1 + (FORCE_EXT if forcing else 0)

            if first:
                val, _ = _pvs(board, child_d, -beta, -alpha,
                               ply + 1, t0, tl)
                val = -val
            else:
                # narrow window / re-search if needed
                val, _ = _pvs(board, child_d - red, -alpha - 1, -alpha,
                               ply + 1, t0, tl)
                val = -val
                if alpha < val < beta:
                    val, _ = _pvs(board, child_d, -beta, -alpha,
                                   ply + 1, t0, tl)
                    val = -val
        except TimeoutError:
            board.pop(); raise
        board.pop()

        if val >= beta:
            _record_killer(mv, ply, depth)
            store(key, depth, beta, LOWER, mv)
            return beta, mv
        if val > alpha:
            alpha, best_move = val, mv
        first = False

    store(key, depth, alpha, EXACT if best_move else UPPER, best_move)
    return alpha, best_move


# ───────────── quiescence search ──────────────────────────────
def _quiescence(board: chess.Board, alpha: int, beta: int) -> int:
    stand = evaluate(board)
    if stand >= beta:
        return beta
    if alpha < stand:
        alpha = stand

    for mv in board.legal_moves:
        if not board.is_capture(mv) and mv.promotion is None and \
           not board.gives_check(mv):
            continue
        if see(board, mv, threshold=50) <= 0:
            continue

        board.push(mv)
        score = -_quiescence(board, -beta, -alpha)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


# ───────────── move-ordering helpers ──────────────────────────
def _record_killer(mv: chess.Move, ply: int, depth: int) -> None:
    if mv not in KILLERS[ply]:
        KILLERS[ply][1] = KILLERS[ply][0]
        KILLERS[ply][0] = mv
    HISTORY[mv] = HISTORY.get(mv, 0) + depth * depth


def _ordered_moves(board: chess.Board, ply: int, tt_hit) -> list[chess.Move]:
    moves = list(board.legal_moves)

    if tt_hit and tt_hit.move in moves:
        moves.remove(tt_hit.move)
        moves.insert(0, tt_hit.move)

    moves.sort(key=lambda m: _score(board, m, ply), reverse=True)
    return moves


def _score(board: chess.Board, mv: chess.Move, ply: int) -> int:
    # 1. promotions
    if mv.promotion:
        return 15_000 + 1_000 * PROMO_ORDER[mv.promotion]
    # 2. captures (MVV/LVA) + SEE bonus
    if board.is_capture(mv):
        victim = board.piece_at(mv.to_square)
        if victim is None and board.is_en_passant(mv):
            ep_sq = mv.to_square + (-8 if board.turn else 8)
            victim = board.piece_at(ep_sq)
        v = victim.piece_type if victim else 0
        a = board.piece_at(mv.from_square).piece_type
        return 10_000 + 10 * v - a + see(board, mv)
    # 3. killer moves
    if mv in KILLERS[ply]:
        return 9_000
    # 4. checks
    if board.gives_check(mv):
        return 3_000
    # 5. history heuristic
    return HISTORY.get(mv, 0)
