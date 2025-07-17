import time, chess
from .evaluation import evaluate
from .transposition import zobrist_hash, probe, store, EXACT, LOWER, UPPER
from .tablebase import tb_best, in_tb  # Added for tablebase integration
from .see import see  # Added for SEE in ordering
import random

INF = 10_000
MAX_PLY = 64
KILLERS = [[None, None] for _ in range(MAX_PLY)]
HISTORY = {}
DELTA_MARGIN = 900  # Queen value for delta pruning

def find_best_move(board: chess.Board, time_limit: float = 2.0):
    best_move = None
    depth = 1
    t_start = time.time()
    aspiration = 30
    score = 0
    while True:
        alpha = score - aspiration
        beta = score + aspiration
        while True:
            try:
                score, move = alphabeta(board, depth, alpha, beta, 0, t_start, time_limit)
            except TimeoutError:
                return best_move or random.choice(list(board.legal_moves))
            if score <= alpha:
                alpha -= aspiration
                continue
            if score >= beta:
                beta += aspiration
                continue
            break
        if move:
            best_move = move
        depth += 1
        if time.time() - t_start > time_limit or depth > MAX_PLY:
            return best_move

def alphabeta(board, depth, alpha, beta, ply, t_start, time_limit):
    if time.time() - t_start > time_limit:
        raise TimeoutError

    # Tablebase probe (new: check early for endgames)
    if in_tb(board):
        tb_move = tb_best(board)
        if tb_move:
            return (INF if board.turn else -INF, tb_move)  # Adjust score based on win/loss

    if board.is_checkmate():
        return (-INF + ply, None)
    if board.is_stalemate() or board.is_insufficient_material():
        return (0, None)
    if depth == 0:
        return (quiescence(board, alpha, beta, ply), None)

    hash_key = zobrist_hash(board)
    tt_entry = probe(hash_key)
    if tt_entry is not None:
        tt_depth, tt_score, tt_flag, tt_move = tt_entry
        if tt_depth >= depth:
            if tt_flag == EXACT:
                return (tt_score, tt_move)
            if tt_flag == LOWER and tt_score > alpha:
                alpha = tt_score
            elif tt_flag == UPPER and tt_score < beta:
                beta = tt_score
            if alpha >= beta:
                return (tt_score, tt_move)

    best_move = None
    legal_moves = list(board.legal_moves)
    if tt_entry is not None and tt_move in legal_moves:
        legal_moves.remove(tt_move)
        legal_moves.insert(0, tt_move)

    legal_moves.sort(key=lambda m: move_score(board, m, ply), reverse=True)

    for idx, move in enumerate(legal_moves):
        new_depth = depth - 1
        # Late Move Reduction (new: reduce depth for later moves if not in check)
        if idx >= 4 and depth >= 3 and not board.is_check() and not board.is_capture(move):
            new_depth -= 1

        board.push(move)
        try:
            score, _ = alphabeta(board, new_depth, -beta, -alpha, ply + 1, t_start, time_limit)
            score = -score
        except TimeoutError:
            board.pop()
            raise
        board.pop()

        if score >= beta:
            if move not in KILLERS[ply]:
                KILLERS[ply][1] = KILLERS[ply][0]
                KILLERS[ply][0] = move
            HISTORY[move] = HISTORY.get(move, 0) + depth * depth
            store(hash_key, depth, beta, LOWER, move)
            return (beta, move)
        if score > alpha:
            alpha, best_move = score, move

    flag = EXACT if best_move else UPPER
    if best_move is not None:
        store(hash_key, depth, alpha, flag, best_move)
    return (alpha, best_move)

def quiescence(board, alpha, beta, ply):
    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    # Delta pruning (new: if even max gain can't help, prune)
    if stand_pat < alpha - DELTA_MARGIN:
        return alpha

    for move in sorted(board.legal_moves, key=lambda m: move_score(board, m, ply), reverse=True):
        if not board.is_capture(move):
            continue
        # SEE filter (new: skip bad captures)
        if see(board, move) < 0:
            continue
        board.push(move)
        score = -quiescence(board, -beta, -alpha, ply + 1)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
        # Limit quiescence depth (new: prevent infinite recursion)
        if ply > 10:
            break
    return alpha

def move_score(board, move, ply):
    if board.is_capture(move):
        victim_piece = board.piece_at(move.to_square)
        if victim_piece is None and board.is_en_passant(move):
            ep_sq = move.to_square + (-8 if board.turn else 8)
            victim_piece = board.piece_at(ep_sq)
        victim_val = victim_piece.piece_type if victim_piece else 0
        attacker_val = board.piece_at(move.from_square).piece_type
        # Improved: Use SEE for accurate capture score
        return 10_000 + see(board, move) + 10 * victim_val - attacker_val
    if move in KILLERS[ply]:
        return 9_000
    return HISTORY.get(move, 0)
