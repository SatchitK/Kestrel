import time, chess
from .evaluation import evaluate
from .transposition import zobrist_hash, probe, store, EXACT, LOWER, UPPER
import random

INF = 10_000
MAX_PLY = 64

# killer moves & history heuristic
KILLERS = [[None, None] for _ in range(MAX_PLY)]
HISTORY = {}

def find_best_move(board: chess.Board, time_limit: float = 2.0):
    """
    Iterative-deepening root. Returns the best chess.Move found
    within `time_limit` seconds (wall-clock). Never raises TimeoutError.
    """
    best_move = None
    depth     = 1
    t_start   = time.time()
    aspiration = 30     # ± window in centipawns
    score = 0

    while True:
        alpha = score - aspiration
        beta  = score + aspiration
        while True:
            try:
                score, move = alphabeta(board, depth, alpha, beta,
                                        0, t_start, time_limit)
            except TimeoutError:
                # Clock expired inside the search – return current best
                return best_move or random.choice(list(board.legal_moves))

            if score <= alpha:           # fail-low, widen window
                alpha -= aspiration
                continue
            if score >= beta:            # fail-high
                beta += aspiration
                continue
            break                        # score inside window

        if move:
            best_move = move

        depth += 1
        if time.time() - t_start > time_limit or depth > MAX_PLY:
            return best_move


# ───────────────────────────────────────────────────────────────
def alphabeta(board, depth, alpha, beta, ply, t_start, time_limit):
    """
    Negamax α-β with TT, LMR, quiescence, killers, history & iterative deepening queue.
    Returns (score, best_move) from perspective of side to move.
    """
    if board.is_checkmate():
        return (-INF + ply, None)
    if board.is_stalemate() or board.is_insufficient_material():
        return (0, None)
    if depth == 0:
        return (quiescence(board, alpha, beta, ply), None)

    # time check
    if time.time() - t_start > time_limit:
        raise TimeoutError

    hash_key = zobrist_hash(board)
    tt = probe(hash_key)
    if tt and tt.depth >= depth:
        if tt.flag == EXACT:
            return (tt.score, tt.move)
        if tt.flag == LOWER and tt.score > alpha:
            alpha = tt.score
        elif tt.flag == UPPER and tt.score < beta:
            beta = tt.score
        if alpha >= beta:
            return (tt.score, tt.move)

    best_move = None
    legal_moves = list(board.legal_moves)
    # move ordering ▸ 1) TT move  2) captures MVV/LVA  3) killers  4) history
    if tt and tt.move in legal_moves:
        legal_moves.remove(tt.move)
        legal_moves.insert(0, tt.move)

    legal_moves.sort(key=lambda m: move_score(board, m, ply), reverse=True)

    for idx, move in enumerate(legal_moves):
        # Late Move Reduction
        new_depth = depth - 1
        if idx >= 4 and depth >= 3 and not board.is_check():
            new_depth -= 1

        board.push(move)
        try:
            score, _ = alphabeta(board, new_depth, -beta, -alpha,
                                 ply + 1, t_start, time_limit)
            score = -score
        except TimeoutError:
            board.pop()
            raise
        board.pop()

        if score >= beta:
            # beta cutoff ▸ store killer / history
            if move not in KILLERS[ply]:
                KILLERS[ply][1] = KILLERS[ply][0]
                KILLERS[ply][0] = move
            HISTORY[move] = HISTORY.get(move, 0) + depth * depth
            store(hash_key, depth, beta, LOWER, move)
            return (beta, move)
        if score > alpha:
            alpha, best_move = score, move

    flag = EXACT if best_move else UPPER
    store(hash_key, depth, alpha, flag, best_move)
    return (alpha, best_move)

# ───────────────────────────────────────────────────────────────
def quiescence(board, alpha, beta, ply):
    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    for move in sorted(board.legal_moves, key=lambda m: board.is_capture(m)):
        if not board.is_capture(move):
            continue
        board.push(move)
        score = -quiescence(board, -beta, -alpha, ply + 1)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

# ───────────────────────────────────────────────────────────────
def move_score(board, move, ply):
    """
    MVV/LVA + killer + history ordering.
    Returns a numeric key used for sorting; higher = searched first.
    """
    # 1. Captures ▸ MVV/LVA
    if board.is_capture(move):
        victim_piece = board.piece_at(move.to_square)
        # en-passant: victim is on a different square
        if victim_piece is None and board.is_en_passant(move):
            ep_sq = move.to_square + (-8 if board.turn else 8)
            victim_piece = board.piece_at(ep_sq)

        victim_val   = victim_piece.piece_type if victim_piece else 0
        attacker_val = board.piece_at(move.from_square).piece_type
        return 10_000 + 10 * victim_val - attacker_val

    # 2. Killer moves
    if move in KILLERS[ply]:
        return 9_000

    # 3. History heuristic
    return HISTORY.get(move, 0)

