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

import torch
import chess

def board_to_tensor(board: chess.Board):
    tensor = torch.zeros(12, 8, 8, dtype=torch.float32)
    piece_map = board.piece_map()
    for square, piece in piece_map.items():
        piece_type = piece.piece_type - 1
        color_offset = 0 if piece.color == chess.WHITE else 6
        row = chess.square_rank(square)
        col = chess.square_file(square)
        tensor[piece_type + color_offset, row, col] = 1
    return tensor


# material weights for supervised training
_WEIGHTS = torch.tensor([
     1,  3,  3.3,  5,  9,  0,     # white pieces
    -1, -3, -3.3, -5, -9,  0      # black pieces
], dtype=torch.float32).view(12, 1, 1)

def material_from_tensor(t):
    return (t * _WEIGHTS).sum(dim=(-3, -2, -1))
