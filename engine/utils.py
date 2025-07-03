import torch
import chess

import torch, chess

# piece index -> plane number (0-5 white, 6-11 black)
_piece_idx = {
    chess.PAWN:   0,
    chess.KNIGHT: 1,
    chess.BISHOP: 2,
    chess.ROOK:   3,
    chess.QUEEN:  4,
    chess.KING:   5,
}

def board_to_tensor(board):
    planes = torch.zeros(12, 8, 8, dtype=torch.float32)
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None:
            continue
        plane = _piece_idx[piece.piece_type] + (0 if piece.color else 6)
        r, f = divmod(sq, 8)
        planes[plane, 7 - r, f] = 1
    return planes

# material weights for supervised training
_WEIGHTS = torch.tensor([
     1,  3,  3.3,  5,  9,  0,     # white pieces
    -1, -3, -3.3, -5, -9,  0      # black pieces
], dtype=torch.float32).view(12, 1, 1)

def material_from_tensor(t):
    return (t * _WEIGHTS).sum(dim=(-3, -2, -1))
