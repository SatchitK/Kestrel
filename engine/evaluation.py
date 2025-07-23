import chess

# --- Piece Values ---
INF = 100000

VAL = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# --- Piece-Square Tables (PSTs) ---
PST = {
    chess.PAWN: [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5,-10, 0, 0,-10, -5, 5,
        5, 10, 10,-20,-20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    chess.KNIGHT: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20, 0, 0, 0, 0,-20,-40,
        -30, 0, 10, 15, 15, 10, 0,-30,
        -30, 5, 15, 20, 20, 15, 5,-30,
        -30, 0, 15, 20, 20, 15, 0,-30,
        -30, 5, 10, 15, 15, 10, 5,-30,
        -40,-20, 0, 5, 5, 0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    chess.BISHOP: [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10, 0, 0, 0, 0, 0, 0,-10,
        -10, 0, 5, 10, 10, 5, 0,-10,
        -10, 5, 5, 10, 10, 5, 5,-10,
        -10, 0, 10, 10, 10, 10, 0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10, 5, 0, 0, 0, 0, 5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    chess.ROOK: [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, 10, 10, 10, 10, 5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        0, 0, 0, 5, 5, 0, 0, 0
    ],
    chess.QUEEN: [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10, 0, 0, 0, 0, 0, 0,-10,
        -10, 0, 5, 5, 5, 5, 0,-10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0,-10,
        -10, 0, 5, 0, 0, 0, 0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ],
    chess.KING: [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20
    ]
}

def is_endgame(board: chess.Board) -> bool:
    """Detect if we're in an endgame phase - FIXED VERSION"""
    # FIXED: Use len() for SquareSet objects, chess.popcount() for integers
    piece_count = chess.popcount(board.occupied) - len(board.pieces(chess.PAWN, chess.WHITE)) - len(board.pieces(chess.PAWN, chess.BLACK))
    return piece_count <= 8  # 8 pieces or fewer (excluding pawns)

def endgame_progress_bonus(board: chess.Board, color: chess.Color) -> int:
    """Reward progress in winning endgames"""
    if not is_endgame(board):
        return 0
    
    bonus = 0
    
    # Material advantage
    white_material = sum(VAL[p.piece_type] for p in board.piece_map().values() if p.color == chess.WHITE and p.piece_type != chess.KING)
    black_material = sum(VAL[p.piece_type] for p in board.piece_map().values() if p.color == chess.BLACK and p.piece_type != chess.KING)
    
    material_diff = white_material - black_material
    if color == chess.BLACK:
        material_diff = -material_diff
    
    # If we have significant material advantage, reward centralization and activity
    if material_diff > 200:  # We're winning
        king_sq = board.king(color)
        if king_sq:
            # Reward king activity in endgame
            king_file = chess.square_file(king_sq)
            king_rank = chess.square_rank(king_sq)
            # Distance from center
            center_distance = max(abs(king_file - 3.5), abs(king_rank - 3.5))
            bonus += int((3.5 - center_distance) * 10)  # Up to 35 bonus for central king
        
        # Reward active pieces
        for piece_type in [chess.ROOK, chess.QUEEN]:
            for sq in board.pieces(piece_type, color):
                # Reward pieces on central files/ranks
                file_centrality = 3.5 - abs(chess.square_file(sq) - 3.5)
                rank_centrality = 3.5 - abs(chess.square_rank(sq) - 3.5)
                bonus += int((file_centrality + rank_centrality) * 2)
        
        # Small bonus just for being in a winning endgame to encourage play
        bonus += 50
    
    return bonus

def fifty_move_penalty(board: chess.Board) -> int:
    """Penalize approaching 50-move rule in winning positions"""
    if board.halfmove_clock > 40:
        # Heavy penalty as we approach 50 moves without progress
        return (board.halfmove_clock - 40) * 20
    return 0

def passed_pawn_bonus(board: chess.Board, color: chess.Color) -> int:
    bonus = 0
    my_pawns = board.pieces(chess.PAWN, color)
    
    for sq in my_pawns:
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        passed = True
        
        for df in [-1, 0, 1]:
            nf = f + df
            if 0 <= nf <= 7:
                ahead_squares = []
                if color == chess.WHITE:
                    for nr in range(r + 1, 8):
                        ahead_squares.append(chess.square(nf, nr))
                else:
                    for nr in range(r - 1, -1, -1):
                        ahead_squares.append(chess.square(nf, nr))
                
                for ahead_sq in ahead_squares:
                    piece = board.piece_at(ahead_sq)
                    if piece and piece.piece_type == chess.PAWN and piece.color != color:
                        passed = False
                        break
                if not passed:
                    break
        
        if passed:
            rank_bonus = [0, 10, 20, 30, 50, 75, 100, 0]
            rank_idx = r if color == chess.WHITE else 7 - r
            # INCREASED bonus for passed pawns in endgame
            multiplier = 2 if is_endgame(board) else 1
            bonus += rank_bonus[rank_idx] * multiplier
    
    return bonus

def pawn_structure_bonus(board: chess.Board, color: chess.Color) -> int:
    bonus = 0
    pawns = board.pieces(chess.PAWN, color)
    
    for sq in pawns:
        f = chess.square_file(sq)
        
        # Doubled pawns
        file_pawns = board.pieces(chess.PAWN, color) & chess.BB_FILES[f]
        if len(file_pawns) > 1:
            bonus -= 15
        
        # Isolated pawns
        isolated = True
        for df in [-1, 1]:
            nf = f + df
            if 0 <= nf <= 7:
                if board.pieces(chess.PAWN, color) & chess.BB_FILES[nf]:
                    isolated = False
                    break
        if isolated:
            bonus -= 20
    
    return bonus

def king_safety(board: chess.Board, color: chess.Color) -> int:
    safety = 0
    king_sq = board.king(color)
    if king_sq is None: 
        return 0
    
    # In endgame, we want active kings, not safe ones
    if is_endgame(board):
        return 0  # Skip pawn shield bonus in endgame
    
    k_file = chess.square_file(king_sq)
    shield_bonus = 0
    
    for f_offset in [-1, 0, 1]:
        f = k_file + f_offset
        if 0 <= f <= 7:
            if color == chess.WHITE:
                if board.piece_at(chess.square(f, 1)) == chess.Piece(chess.PAWN, chess.WHITE):
                    shield_bonus += 15
                if board.piece_at(chess.square(f, 2)) == chess.Piece(chess.PAWN, chess.WHITE):
                    shield_bonus += 10
            else:
                if board.piece_at(chess.square(f, 6)) == chess.Piece(chess.PAWN, chess.BLACK):
                    shield_bonus += 15
                if board.piece_at(chess.square(f, 5)) == chess.Piece(chess.PAWN, chess.BLACK):
                    shield_bonus += 10
    
    safety += shield_bonus
    return safety

def mobility_bonus(board: chess.Board, color: chess.Color) -> int:
    bonus = 0
    for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        for sq in board.pieces(piece_type, color):
            mobility = len(board.attacks(sq))
            # INCREASED mobility bonus in endgame
            multiplier = 2 if is_endgame(board) else 1
            bonus += mobility * multiplier
    return bonus

def evaluate(board: chess.Board) -> int:
    if board.is_checkmate():
        return -INF
    
    # MODIFIED: Distinguish between different types of draws
    if board.is_stalemate() or board.is_insufficient_material():
        return 0  # True draws
    
    # Penalize approaching draw by repetition or 50-move rule if we're winning
    if board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return 0  # Forced draws
    
    score = 0
    
    # Material and PST
    for sq, piece in board.piece_map().items():
        val = VAL[piece.piece_type]
        pst_sq = sq if piece.color == chess.WHITE else chess.square_mirror(sq)
        pst_val = PST[piece.piece_type][pst_sq]
        term = val + pst_val
        score += term if piece.color == chess.WHITE else -term
    
    # Bonuses
    white_bonus = passed_pawn_bonus(board, chess.WHITE) + \
                  pawn_structure_bonus(board, chess.WHITE) + \
                  king_safety(board, chess.WHITE) + \
                  mobility_bonus(board, chess.WHITE) + \
                  endgame_progress_bonus(board, chess.WHITE)
    
    black_bonus = passed_pawn_bonus(board, chess.BLACK) + \
                  pawn_structure_bonus(board, chess.BLACK) + \
                  king_safety(board, chess.BLACK) + \
                  mobility_bonus(board, chess.BLACK) + \
                  endgame_progress_bonus(board, chess.BLACK)
    
    score += white_bonus - black_bonus
    
    # Apply 50-move penalty to the winning side
    if score > 100:  # White is winning
        score -= fifty_move_penalty(board) if board.turn == chess.WHITE else 0
    elif score < -100:  # Black is winning
        score += fifty_move_penalty(board) if board.turn == chess.BLACK else 0
    
    return score if board.turn == chess.WHITE else -score
