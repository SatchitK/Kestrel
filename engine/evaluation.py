import chess

MG_VAL = {
    chess.PAWN: 82,
    chess.KNIGHT: 337,
    chess.BISHOP: 365,
    chess.ROOK: 477,
    chess.QUEEN: 1025,
    chess.KING: 0
}

EG_VAL = {
    chess.PAWN: 94,
    chess.KNIGHT: 281,
    chess.BISHOP: 297,
    chess.ROOK: 512,
    chess.QUEEN: 936,
    chess.KING: 0
}

MG_PST = {
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

EG_PST = {
    chess.PAWN: [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, -20, -20, 10, 10, 5,
        5, -5, -10, 0, 0, -10, -5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, 5, 10, 25, 25, 10, 5, 5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    chess.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    chess.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 10, 5, 0, 0, 5, 10, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    chess.ROOK: [
        0, 0, 0, 5, 5, 0, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 10, 10, 10, 10, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    chess.QUEEN: [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -10, 5, 5, 5, 5, 5, 0, -10,
        0, 0, 5, 5, 5, 5, 0, -5,
        -5, 0, 5, 5, 5, 5, 0, -5,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ],
    chess.KING: [
        -50, -30, -30, -30, -30, -30, -30, -50,
        -30, -30, 0, 0, 0, 0, -30, -30,
        -20, -10, 20, 20, 20, 20, -10, -20,
        -10, 20, 20, 40, 40, 20, 20, -10,
        -10, 20, 30, 40, 40, 30, 20, -10,
        -10, 20, 20, 40, 40, 20, 20, -10,
        -20, -10, 20, 20, 20, 20, -10, -20,
        -30, -20, -10, 0, 0, -10, -20, -30
    ]
}

def get_phase(board: chess.Board) -> float:
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    rooks = len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK))
    minors = (len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK)) +
              len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK)))
    total_phase = queens * 4 + rooks * 2 + minors * 1
    return min(total_phase / 24.0, 1.0)  # Phase 1.0 = opening, 0.0 = endgame

def passed_pawn_bonus(board: chess.Board) -> int:
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
    if file_idx > 0 and pawn_bb & chess.BB_FILES[file_idx - 1]:
        return True
    if file_idx < 7 and pawn_bb & chess.BB_FILES[file_idx + 1]:
        return True
    return False

def king_safety(board: chess.Board) -> int:
    if board.fullmove_number < 10:
        return 0
    k_sq = board.king(board.turn)
    if k_sq is None:
        return 0
    file = chess.square_file(k_sq)
    safety = -25 if file in (3, 4) else 0
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
    bonus = 0
    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)
        sign = 1 if color == board.turn else -1
        for sq in pawns:
            f = chess.square_file(sq)
            if not _adjacent_file_has_pawn(f, pawns):
                bonus += sign * -15
            file_pawns = len(pawns & chess.BB_FILES[f])
            if file_pawns > 1:
                bonus += sign * -10 * (file_pawns - 1)
    return bonus

def mobility_bonus(board: chess.Board) -> int:
    bonus = 0
    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == board.turn else -1
        knights = board.pieces(chess.KNIGHT, color)
        bishops = board.pieces(chess.BISHOP, color)
        for sq in knights:
            attacks = board.attacks(sq)
            bonus += sign * len(attacks) * 2
        for sq in bishops:
            attacks = board.attacks(sq)
            bonus += sign * len(attacks) * 1.5
    return int(bonus)

def evaluate(board: chess.Board) -> int:
    phase = get_phase(board)
    mg_score = 0
    eg_score = 0
    for sq, piece in board.piece_map().items():
        mirror_sq = sq if piece.color == chess.WHITE else chess.square_mirror(sq)
        mg_val = MG_VAL[piece.piece_type] + MG_PST[piece.piece_type][mirror_sq]
        eg_val = EG_VAL[piece.piece_type] + EG_PST[piece.piece_type][mirror_sq]
        sign = 1 if piece.color == board.turn else -1
        mg_score += sign * mg_val
        eg_score += sign * eg_val

    # Additional bonuses (tapered where appropriate)
    passed_bonus = passed_pawn_bonus(board) * (1 + (1 - phase))  # Boost in endgame
    king_safe = king_safety(board) if phase > 0.5 else 0  # Only in midgame
    pawn_struct = pawn_structure_bonus(board)
    mob_bonus = mobility_bonus(board)

    mg_score += passed_bonus + king_safe + pawn_struct + mob_bonus
    eg_score += passed_bonus + king_safe + pawn_struct + mob_bonus

    # Tapered score
    score = int(mg_score * phase + eg_score * (1 - phase))

    # Crude mobility adjustment (original, kept for consistency)
    score += 4 * board.legal_moves.count()
    board.turn = not board.turn
    score -= 4 * board.legal_moves.count()
    board.turn = not board.turn

    return score
