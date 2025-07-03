import chess
from gui.gui_constants import NUM_SQ as SQ, LIGHT_SQ_COLOR as LIGHT, DARK_SQ_COLOR as DARK, WHITE_BOTTOM as white_bottom


# square to pixel coordinates
# converts a chess square index to pixel coordinates on the board
def sq2xy(sq):
    f, r = chess.square_file(sq), chess.square_rank(sq)
    return (f*SQ, (7-r)*SQ) if white_bottom else ((7-f)*SQ, r*SQ)

def xy2sq(x, y):
    col, row = x//SQ, y//SQ
    if 0 <= col < 8 and 0 <= row < 8:
        return chess.square(col, 7-row) if white_bottom else chess.square(7-col, row)
    return None