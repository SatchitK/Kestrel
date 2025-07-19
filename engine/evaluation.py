import chess

VAL = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

PST = {
    chess.PAWN: [
        0, 5, 5, -5, -5, 10, 50, 0,
        0, 10, -5, 0, 0, 10, 50, 0,
        0, 10, -10, 20, 25, 30, 50, 0,
        0, -20, 0, 0, 25, 30, 50, 0,
        0, 10, -5, 0, 25, 30, 50, 0,
        0, 10, -5, 0, 0, 10, 50, 0,
        0, 10, -10, -5, -5, 10, 50, 0,
        0, 5, 5, -5, -5, 10, 50, 0
    ],
    chess.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    chess.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    chess.ROOK: [
        0, 0, 5, 10, 10, 5, 0, 0,
        0, 0, 5, 10, 10, 5, 0, 0,
        0, 0, 5, 10, 10, 5, 0, 0,
        0, 0, 5, 10, 10, 5, 0, 0,
        0, 0, 5, 10, 10, 5, 0, 0,
        0, 0, 5, 10, 10, 5, 0, 0,
        25, 25, 25, 25, 25, 25, 25, 25,
        0, 0, 5, 10, 10, 5, 0, 0
    ],
    chess.QUEEN: [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ],
    chess.KING: [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20
    ]
}

def passed_pawn_bonus(board: chess.Board) -> int:
    # Original function unchanged
    side = board.turn
    my_pawns = board.pieces(chess.PAWN, side)
    opp_pawns = board.pieces(chess.PAWN, not side)
    bonus = 0
    for sq in my_pawns:
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        blocked = False
        for df in (-1, 0, 1):
            nf = f + df
            if not 0 <= nf <= 7:
                continue
            if side == chess.WHITE:
                ahead = (chess.square(nf, nr) for nr in range(r + 1, 8))
            else:
                ahead = (chess.square(nf, nr) for nr in range(r - 1, -1, -1))
            if any(sq2 in opp_pawns for sq2 in ahead):
                blocked = True
                break
        if blocked:
            continue
        rank_from_white = r if side == chess.WHITE else 7 - r
        bonus += (rank_from_white + 1) * 10
    return bonus

def _adjacent_file_has_pawn(file_idx: int, pawn_bb: chess.SquareSet) -> bool:
    # Original function unchanged
    if file_idx > 0 and pawn_bb & chess.BB_FILES[file_idx - 1]:
        return True
    if file_idx < 7 and pawn_bb & chess.BB_FILES[file_idx + 1]:
        return True
    return False

def king_safety(board: chess.Board) -> int:
    # Improved: Added pawn shield bonus
    if board.fullmove_number < 10:
        return 0
    k_sq = board.king(board.turn)
    if k_sq is None:
        return 0
    file = chess.square_file(k_sq)
    safety = -25 if file in (3, 4) else 0
    # Pawn shield: bonus for pawns in front of king
    shield_files = [file-1, file, file+1]
    shield_bonus = 0
    for f in shield_files:
        if 0 <= f <= 7:
            pawn_mask = chess.BB_FILES[f] & (chess.BB_RANKS[1] if board.turn == chess.WHITE else chess.BB_RANKS[6])
            if board.pieces(chess.PAWN, board.turn) & pawn_mask:
                shield_bonus += 10
    safety += shield_bonus
    return safety

def pawn_structure_bonus(board: chess.Board) -> int:
    # New: Penalties for isolated and doubled pawns
    bonus = 0
    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)
        sign = 1 if color == board.turn else -1
        for sq in pawns:
            f = chess.square_file(sq)
            # Isolated pawn
            if not _adjacent_file_has_pawn(f, pawns):
                bonus += sign * -15
            # Doubled pawn
            file_pawns = len(pawns & chess.BB_FILES[f])
            if file_pawns > 1:
                bonus += sign * -10 * (file_pawns - 1)
    return bonus

def mobility_bonus(board: chess.Board) -> int:
    # New: Simple mobility (number of legal moves per piece type)
    bonus = 0
    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == board.turn else -1
        knights = board.pieces(chess.KNIGHT, color)
        bishops = board.pieces(chess.BISHOP, color)
        for sq in knights:
            attacks = board.attacks(sq)
            bonus += sign * len(attacks) * 2  # Knights get 2cp per move
        for sq in bishops:
            attacks = board.attacks(sq)
            bonus += sign * len(attacks) * 1.5  # Bishops get 1.5cp per move
    return int(bonus)

def evaluate(board: chess.Board) -> int:
    score = 0
    for sq, piece in board.piece_map().items():
        val = VAL[piece.piece_type]
        pst = PST[piece.piece_type][sq if piece.color else chess.square_mirror(sq)]
        term = val + pst
        score += term if piece.color == board.turn else -term

    # Mobility (improved: now includes all pieces roughly)
    score += 4 * board.legal_moves.count()
    board.turn = not board.turn
    score -= 4 * board.legal_moves.count()
    board.turn = not board.turn

    # Additional bonuses
    score += passed_pawn_bonus(board)
    score += king_safety(board)
    score += pawn_structure_bonus(board)
    score += mobility_bonus(board)

    return score
