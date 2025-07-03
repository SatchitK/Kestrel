import tkinter as tk
import chess
from gui.gui_constants import NUM_SQ as SQ, LIGHT_SQ_COLOR as LIGHT, DARK_SQ_COLOR as DARK, WHITE_BOTTOM as white_bottom
from gui.gui_helpers import sq2xy

root = tk.Tk()
root.title("Kestrel")

logo = tk.PhotoImage(file="github-assets/kestrel_icon_logo.png")
root.iconphoto(True, logo)

canvas = tk.Canvas(root, width=8*SQ, height=8*SQ)
canvas.pack()

board = chess.Board()

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
            if piece.color:
                fill_color = "black" if piece.color else "white"
            piece_x_coord = x + SQ // 2
            piece_y_coord = y + SQ // 2
            font_characteristics = ("Arial", 24)
            canvas.create_text(piece_x_coord, piece_y_coord, text=piece.symbol(), font=font_characteristics, fill=fill_color)

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