import time, chess, random
from .evaluation import evaluate
from .transposition import zobrist_hash, probe, store, EXACT, LOWER, UPPER, unpack_move
from .tablebase import tb_best, in_tb
from .see import see

INF = 32000
MAX_PLY = 64
KILLERS = [[None, None] for _ in range(MAX_PLY)]
HISTORY = {}

def find_best_move(board: chess.Board, time_limit: float):
    best_move = None
    depth = 1
    t_start = time.time()
    score = 0
    nodes = 0
    
    while True:
        aspiration = 30
        alpha, beta = score - aspiration, score + aspiration
        
        try:
            current_score, move, searched_nodes = alphabeta(board, depth, alpha, beta, 0, t_start, time_limit)
            nodes += searched_nodes
            
            if current_score <= alpha or current_score >= beta:
                alpha, beta = -INF, INF
                current_score, move, searched_nodes = alphabeta(board, depth, alpha, beta, 0, t_start, time_limit)
                nodes += searched_nodes
            
            score = current_score
            
        except TimeoutError:
            return best_move or random.choice(list(board.legal_moves))
        
        if move:
            best_move = move
        
        elapsed_time = time.time() - t_start
        nps = int(nodes / elapsed_time) if elapsed_time > 0 else 0
        print(f"info depth {depth} score cp {score} nodes {nodes} nps {nps} time {int(elapsed_time * 1000)} pv {best_move.uci()}")
        
        depth += 1
        
        if elapsed_time > time_limit * 0.7 or depth > MAX_PLY:
            return best_move

def alphabeta(board, depth, alpha, beta, ply, t_start, time_limit):
    if time.time() - t_start > time_limit:
        raise TimeoutError
    
    nodes = 1
    
    if ply > 0 and (board.is_checkmate() or board.is_stalemate()):
        return evaluate(board), None, nodes
    
    # NEW: Penalize repetitions if we're winning
    if ply > 0 and board.is_repetition():
        eval_score = evaluate(board)
        if eval_score > 50:  # We're winning, penalize repetition
            return eval_score - 100, None, nodes
        return eval_score, None, nodes
    
    # Tablebase Probe
    if in_tb(board) and ply > 0 and (tb_move := tb_best(board)):
        return INF - ply, tb_move, nodes
    
    if depth <= 0:
        q_score, q_nodes = quiescence(board, alpha, beta, ply)
        return q_score, None, nodes + q_nodes
    
    hash_key = zobrist_hash(board)
    tt_entry = probe(hash_key)
    tt_move = None
    
    if tt_entry:
        tt_depth, tt_score, tt_flag, tt_move_int = tt_entry
        tt_move = unpack_move(board, tt_move_int)
        
        if tt_depth >= depth and ply > 0:
            if tt_flag == EXACT: return tt_score, tt_move, nodes
            if tt_flag == LOWER and tt_score >= beta: return tt_score, tt_move, nodes
            if tt_flag == UPPER and tt_score <= alpha: return tt_score, tt_move, nodes
    
    # Null Move Pruning
    if depth >= 3 and not board.is_check() and ply > 0 and board.peek() != chess.Move.null():
        board.push(chess.Move.null())
        null_score, _, s_nodes = alphabeta(board, depth - 3, -beta, -beta + 1, ply + 1, t_start, time_limit)
        nodes += s_nodes
        board.pop()
        
        if -null_score >= beta:
            return beta, None, nodes
    
    best_move, best_score = None, -INF
    
    moves = sorted(list(board.legal_moves), key=lambda m: move_score(board, m, ply, tt_move), reverse=True)
    
    for move in moves:
        board.push(move)
        score, _, s_nodes = alphabeta(board, depth - 1, -beta, -alpha, ply + 1, t_start, time_limit)
        nodes += s_nodes
        score = -score
        board.pop()
        
        if score > best_score:
            best_score, best_move = score, move
        
        if score >= beta:
            if not board.is_capture(move):
                KILLERS[ply][1], KILLERS[ply][0] = KILLERS[ply][0], move
                HISTORY[move] = HISTORY.get(move, 0) + depth * depth
            
            store(hash_key, depth, beta, LOWER, move)
            return beta, move, nodes
        
        if score > alpha:
            alpha = score
    
    flag = EXACT if best_score > -INF else UPPER
    if best_move:
        store(hash_key, depth, best_score, flag, best_move)
    
    return alpha, best_move, nodes

def quiescence(board, alpha, beta, ply):
    nodes = 1
    stand_pat = evaluate(board)
    
    if stand_pat >= beta: return beta, nodes
    if alpha < stand_pat: alpha = stand_pat
    
    captures = sorted([m for m in board.legal_moves if board.is_capture(m)], key=lambda m: see(board, m), reverse=True)
    
    for move in captures:
        if see(board, move) < 0: continue
        
        board.push(move)
        score, s_nodes = quiescence(board, -beta, -alpha, ply + 1)
        nodes += s_nodes
        score = -score
        board.pop()
        
        if score >= beta: return beta, nodes
        if score > alpha: alpha = score
    
    return alpha, nodes

def move_score(board, move, ply, tt_move):
    if move == tt_move: return 20000
    if board.is_capture(move): return 10000 + see(board, move)
    
    # NEW: Bonus for pawn moves in endgames (progress!)
    piece = board.piece_at(move.from_square)
    if piece and piece.piece_type == chess.PAWN:
        return 1000  # Encourage pawn progress
    
    if move in KILLERS[ply]: return 9000
    return HISTORY.get(move, 0)
