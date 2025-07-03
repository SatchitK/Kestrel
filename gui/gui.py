import tkinter as tk
import chess
import pathlib
from gui.gui_constants import NUM_SQ as SQ, LIGHT_SQ_COLOR as LIGHT, DARK_SQ_COLOR as DARK, WHITE_BOTTOM as white_bottom
from gui.gui_helpers import sq2xy

root = tk.Tk()
root.title("Kestrel")

logo = tk.PhotoImage(file="github-assets/kestrel_icon_logo.png")
root.iconphoto(True, logo)

canvas = tk.Canvas(root, width=8*SQ, height=8*SQ)
canvas.pack()

board = chess.Board()

PIECES_IMG_DIR = pathlib.Path(__file__).parent / "images"
piece_names = PIECES_IMG_DIR.glob("*.png")
IMG = {p.stem: tk.PhotoImage(file=p) for p in piece_names}

def draw():
    canvas.delete("all")
    for r in range(8):
        for c in range(8):
            color = LIGHT if (r + c) % 2 == 0 else DARK
            x = c*SQ if white_bottom else (7-c)*SQ
            y = r*SQ if white_bottom else (7-r)*SQ
            canvas.create_rectangle(x, y, x+SQ, y+SQ, fill=color, width=0)
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            x, y = sq2xy(sq)
            key = ('w' if piece.color else 'b') + piece.symbol().upper()
            canvas.create_image(x, y, anchor="nw", image=IMG[key])

def previous_move():
    if board.move_stack:
        board.pop()
        draw()

def next_move():
    pass

nav_frame = tk.Frame(root)
nav_frame.pack()
tk.Button(nav_frame, text="Previous Move", command=previous_move).pack(side=tk.LEFT)
tk.Button(nav_frame, text="Next Move", command=next_move).pack(side=tk.LEFT)

draw()
root.mainloop()