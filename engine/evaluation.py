import chess

# --- Piece Values ---
INF = 100000  # Added INF for checkmate evaluation
VAL = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000  # King value is high for checkmate detection in search
}

# --- Piece-Square Tables (PSTs) ---
PST = {
    chess.PAWN: [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0
    ],
    chess.KNIGHT: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    chess.BISHOP: [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    chess.ROOK: [
          0,  0,  0,  0,  0,  0,  0,  0,
          5, 10, 10, 10, 10, 10, 10,  5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
          0,  0,  0,  5,  5,  0,  0,  0
    ],
    chess.QUEEN: [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ],
    chess.KING: [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20
    ]
}

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
                else: # BLACK
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
            bonus += rank_bonus[rank_idx]
            
    return bonus

def pawn_structure_bonus(board: chess.Board, color: chess.Color) -> int:
    bonus = 0
    pawns = board.pieces(chess.PAWN, color)
    
    for sq in pawns:
        f = chess.square_file(sq)
        
        # Doubled pawns
        file_pawns = board.pieces(chess.PAWN, color) & chess.BB_FILES[f]
        # CORRECTED LINE: Use len() for SquareSet objects
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
    if king_sq is None: return 0
    
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
            else: # BLACK
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
            bonus += len(board.attacks(sq))
    return bonus

def evaluate(board: chess.Board) -> int:
    if board.is_checkmate():
        # The side to move is checkmated
        return -INF
    if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return 0

    score = 0
    
    # Material and PST
    for sq, piece in board.piece_map().items():
        val = VAL[piece.piece_type]
        # Mirror the square for black's PST lookup
        pst_sq = sq if piece.color == chess.WHITE else chess.square_mirror(sq)
        pst_val = PST[piece.piece_type][pst_sq]
        term = val + pst_val
        score += term if piece.color == chess.WHITE else -term
        
    # Bonuses
    white_bonus = passed_pawn_bonus(board, chess.WHITE) + \
                  pawn_structure_bonus(board, chess.WHITE) + \
                  king_safety(board, chess.WHITE) + \
                  mobility_bonus(board, chess.WHITE)
                  
    black_bonus = passed_pawn_bonus(board, chess.BLACK) + \
                  pawn_structure_bonus(board, chess.BLACK) + \
                  king_safety(board, chess.BLACK) + \
                  mobility_bonus(board, chess.BLACK)

    score += white_bonus - black_bonus
    
    # Return score from the perspective of the current player
    return score if board.turn == chess.WHITE else -score
