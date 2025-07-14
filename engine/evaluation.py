import chess

VAL = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:     0
}

PST = {
    chess.PAWN: [
         0,   5,   5,  -5,  -5,  10,  50,   0,
         0,  10,  -5,   0,   0,  10,  50,   0,
         0,  10, -10,  20,  25,  30,  50,   0,
         0, -20,   0,   0,  25,  30,  50,   0,
         0,  10,  -5,   0,  25,  30,  50,   0,
         0,  10,  -5,   0,   0,  10,  50,   0,
         0,  10, -10,  -5,  -5,  10,  50,   0,
         0,   5,   5,  -5,  -5,  10,  50,   0],
    chess.KNIGHT: [
       -50, -40, -30, -30, -30, -30, -40, -50,
       -40, -20,   0,   0,   0,   0, -20, -40,
       -30,   0,  10,  15,  15,  10,   0, -30,
       -30,   5,  15,  20,  20,  15,   5, -30,
       -30,   0,  15,  20,  20,  15,   0, -30,
       -30,   5,  10,  15,  15,  10,   5, -30,
       -40, -20,   0,   5,   5,   0, -20, -40,
       -50, -40, -30, -30, -30, -30, -40, -50],
    chess.BISHOP: [
       -20, -10, -10, -10, -10, -10, -10, -20,
       -10,   5,   0,   0,   0,   0,   5, -10,
       -10,  10,  10,  10,  10,  10,  10, -10,
       -10,   0,  10,  10,  10,  10,   0, -10,
       -10,   5,   5,  10,  10,   5,   5, -10,
       -10,   0,   5,  10,  10,   5,   0, -10,
       -10,   0,   0,   0,   0,   0,   0, -10,
       -20, -10, -10, -10, -10, -10, -10, -20],
    chess.ROOK: [
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
         0,   0,   5,  10,  10,   5,   0,   0,
        25,  25,  25,  25,  25,  25,  25,  25,
         0,   0,   5,  10,  10,   5,   0,   0],
    chess.QUEEN: [
       -20, -10, -10,  -5,  -5, -10, -10, -20,
       -10,   0,   0,   0,   0,   0,   0, -10,
       -10,   0,   5,   5,   5,   5,   0, -10,
        -5,   0,   5,   5,   5,   5,   0,  -5,
         0,   0,   5,   5,   5,   5,   0,  -5,
       -10,   5,   5,   5,   5,   5,   0, -10,
       -10,   0,   5,   0,   0,   0,   0, -10,
       -20, -10, -10,  -5,  -5, -10, -10, -20],
    chess.KING: [
       -30, -40, -40, -50, -50, -40, -40, -30,
       -30, -40, -40, -50, -50, -40, -40, -30,
       -30, -40, -40, -50, -50, -40, -40, -30,
       -30, -40, -40, -50, -50, -40, -40, -30,
       -20, -30, -30, -40, -40, -30, -30, -20,
       -10, -20, -20, -20, -20, -20, -20, -10,
        20,  20,   0,   0,   0,   0,  20,  20,
        20,  30,  10,   0,   0,  10,  30,  20]
}

def passed_pawn_bonus(board: chess.Board) -> int:
    side      = board.turn
    my_pawns  = board.pieces(chess.PAWN, side)
    opp_pawns = board.pieces(chess.PAWN, not side)
    bonus     = 0

    for sq in my_pawns:
        f   = chess.square_file(sq)
        r   = chess.square_rank(sq)
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
    if file_idx > 0  and pawn_bb & chess.BB_FILES[file_idx - 1]:
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
    return -25 if file in (3, 4) else 0

def evaluate(board: chess.Board) -> int:
    score = 0

    for sq, piece in board.piece_map().items():
        val  = VAL[piece.piece_type]
        pst  = PST[piece.piece_type][sq if piece.color else chess.square_mirror(sq)]
        term = val + pst
        score += term if piece.color == board.turn else -term

    score += 4 * board.legal_moves.count()
    board.turn = not board.turn
    score -= 4 * board.legal_moves.count()
    board.turn = not board.turn

    score += passed_pawn_bonus(board)
    score += king_safety(board)

    return score