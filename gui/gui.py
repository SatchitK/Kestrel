import tkinter as tk
import chess
import pathlib
from gui.gui_constants import NUM_SQ as SQ, LIGHT_SQ_COLOR as LIGHT, DARK_SQ_COLOR as DARK, WHITE_BOTTOM as white_bottom
from gui.gui_helpers import sq2xy, xy2sq

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

drag_item = None
from_sq = None
avail_sqs = set()

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
            canvas.create_image(x, y, anchor="nw", image=IMG[key], tags=f"sq{sq}")

def start_drag(event):
    global drag_item, from_sq, avail_sqs
    if board.is_game_over():
        return
    sq = xy2sq(event.x, event.y)
    if sq is None:
        return
    piece = board.piece_at(sq)
    if piece is None or piece.color != board.turn:
        return
    from_sq = sq
    avail_sqs = {move.to_square for move in board.legal_moves if move.from_square == sq}
    draw()
    ids = canvas.find_withtag(f"sq{sq}")
    drag_item = ids[-1] if ids else None
    if drag_item:
        canvas.tag_raise(drag_item)

def drag(event):
    if drag_item:
        canvas.coords(drag_item, event.x-SQ//2, event.y-SQ//2)

def end_drag(event):
    global drag_item, from_sq, avail_sqs
    if drag_item is None:
        return
    to_sq = xy2sq(event.x, event.y)
    if to_sq is not None and to_sq in avail_sqs:
        move = chess.Move(from_sq, to_sq)
        board.push(move)
    drag_item = None
    from_sq = None
    avail_sqs = set()
    draw()

def previous_move():
    if board.move_stack:
        board.pop()
        draw()

canvas.bind("<Button-1>", start_drag)
canvas.bind("<B1-Motion>", drag)
canvas.bind("<ButtonRelease-1>", end_drag)

nav_frame = tk.Frame(root)
nav_frame.pack()
tk.Button(nav_frame, text="Previous Move", command=previous_move).pack(side=tk.LEFT)

draw()
root.mainloop()