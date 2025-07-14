"""
engine/see.py  •  Static-Exchange Evaluation (SEE)

Returns the centipawn gain for the side to move.  Positive ⇒ good capture.
Implementation: classical swap-list algorithm with a *deterministic*
least-valuable-attacker scan, so forks and similar tactics are scored correctly.
"""
from __future__ import annotations
import chess

# Material values in centipawns
_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
           chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 10_000}


def _piece_value(board: chess.Board, square: int) -> int:
    p = board.piece_at(square)
    return _VALUES[p.piece_type] if p else 0


def see(board: chess.Board, move: chess.Move, threshold: int = 0) -> int:
    """
    Static-exchange evaluation of *move* on *board*.
    If the final net gain ≤ −threshold the capture can be pruned.

    Returns: material gain for the side to move, in centipawns.
    """
    if not board.is_capture(move):
        return 0

    tgt  = move.to_square
    stm  = board.turn
    gain = [_piece_value(board, tgt)]

    occ = board.occupied
    occ ^= chess.BB_SQUARES[move.from_square]     # moving piece leaves
    occ |= chess.BB_SQUARES[tgt]                  # …and lands on target

    side = stm
    while True:
        side ^= chess.WHITE                       # switch sides
        attack_bb = board.attackers_mask(side, tgt) & occ
        if not attack_bb:
            break

        # --- pick *least-valuable* attacker deterministically -------------
        for pt in (chess.PAWN, chess.KNIGHT, chess.BISHOP,
                   chess.ROOK, chess.QUEEN, chess.KING):
            bb = attack_bb & board.pieces_mask(pt, side)
            if bb:
                from_sq = chess.lsb(bb)           # cheapest attacker
                break

        gain.append(_piece_value(board, from_sq) - gain[-1])
        occ ^= chess.BB_SQUARES[from_sq]          # remove captured attacker

    # minimax rollback
    for i in range(len(gain) - 2, -1, -1):
        gain[i] = max(-gain[i + 1], gain[i])
    return gain[0]
