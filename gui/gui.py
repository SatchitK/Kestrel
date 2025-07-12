import tkinter as tk
import chess
import pathlib
import engine                               # ← NEW

from gui.gui_constants import NUM_SQ as SQ, LIGHT_SQ_COLOR as LIGHT, \
                              DARK_SQ_COLOR as DARK, WHITE_BOTTOM as white_bottom
from gui.gui_helpers import sq2xy, xy2sq
import gui.gui_helpers as helpers      # <— NEW


import sys, os, pathlib

def resource_path(relative: str) -> str:
    """
    Return absolute path to a resource, whether the app is frozen
    or running in the source tree.
    """
    base = getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parent.parent)
    return os.path.join(base, relative)


# ──────────────────────────────────────────
# basic window setup
root = tk.Tk()
root.title("Kestrel")
logo = tk.PhotoImage(file=resource_path("assets/kestrel_icon_logo.png"))

PIECES_IMG_DIR = pathlib.Path(resource_path("gui/images"))
IMG = {p.stem: tk.PhotoImage(file=resource_path(str(p)))
       for p in PIECES_IMG_DIR.glob("*.png")}

root.iconphoto(True, logo)

canvas = tk.Canvas(root, width=8*SQ, height=8*SQ)
canvas.pack()

board = chess.Board()

import threading

engine_thinking = False

OVERLAY_BG = "#000000"      # black, 50 % stipple
OVERLAY_FG = "#ffeb3b"      # bright yellow text

# PIECES_IMG_DIR = pathlib.Path(__file__).parent / "images"
# IMG = {p.stem: tk.PhotoImage(file=p) for p in PIECES_IMG_DIR.glob("*.png")}
# human starts with the side that is at the bottom
human_color = chess.WHITE if white_bottom else chess.BLACK

drag_item   = None
from_sq     = None
avail_sqs   = set()
last_move   = None
is_dragging = False
undone_moves = []

# ──────────────────────────────────────────
def draw():
    canvas.delete("all")

    # board squares
    for r in range(8):
        for c in range(8):
            color = LIGHT if (r + c) % 2 == 0 else DARK
            x = c*SQ if white_bottom else (7-c)*SQ
            y = r*SQ if white_bottom else (7-r)*SQ
            canvas.create_rectangle(x, y, x+SQ, y+SQ, fill=color, width=0)

    # last move highlight
    if last_move:
        for sq in (last_move.from_square, last_move.to_square):
            x, y = sq2xy(sq)
            canvas.create_rectangle(x, y, x+SQ, y+SQ,
                                    fill="#f6f669", stipple="gray50")

    # check highlight
    if board.is_check():
        k_sq = board.king(board.turn)
        if k_sq is not None:
            x, y = sq2xy(k_sq)
            canvas.create_rectangle(x, y, x+SQ, y+SQ,
                                    fill="#ff4d4d", stipple="gray50")

    # pieces
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            x, y = sq2xy(sq)
            key = ('w' if piece.color else 'b') + piece.symbol().upper()
            canvas.create_image(x, y, anchor="nw", image=IMG[key],
                                tags=f"sq{sq}")

    # available-move dots
    for sq in avail_sqs:
        x, y = sq2xy(sq)
        cx, cy = x + SQ//2, y + SQ//2
        rdot = SQ // 6
        canvas.create_oval(cx-rdot, cy-rdot, cx+rdot, cy+rdot,
                           fill="#4da6ff", outline="")

    update_status()

    if board.is_checkmate():
        # darken everything below
        canvas.create_rectangle(0, 0, 8*SQ, 8*SQ,
                                fill=OVERLAY_BG, stipple="gray50", width=0)
        # winner text
        winner = "White" if board.turn == chess.BLACK else "Black"
        canvas.create_text(4*SQ, 4*SQ,
                           text=f"{winner} wins by CHECKMATE",
                           fill=OVERLAY_FG,
                           font=("Helvetica", SQ//4, "bold"),
                           anchor="c")

def update_status():
    if board.is_checkmate():
        winner = "White" if board.turn == chess.BLACK else "Black"
        msg = f"Checkmate! {winner} wins!"
    elif board.is_stalemate():
        msg = "Stalemate! Draw."
    elif board.is_insufficient_material():
        msg = "Insufficient material — draw."
    elif board.is_check():
        msg = "Check!"
    else:
        msg = f"{'White' if board.turn else 'Black'} to move"
    status_label.config(text=msg)

# ──────────────────────────────────────────
def make_ai_move():
    """Start a background thread; GUI stays responsive."""
    global engine_thinking
    if board.is_game_over() or board.turn == human_color or engine_thinking:
        return

    position = board.copy()         # thread-safe snapshot
    engine_thinking = True

    def worker():
        move = engine.best_move(position, time_limit=2.0)

        def apply():
            global last_move, engine_thinking, undone_moves
            if move and not board.is_game_over() and board.turn != human_color:
                board.push(move)
                last_move = move
                undone_moves.clear()
                draw()
            engine_thinking = False

        root.after(0, apply)        # back to GUI thread

    threading.Thread(target=worker, daemon=True).start()


# ──────────────────────────────────────────
# mouse handlers
def start_drag(event):
    global drag_item, from_sq, avail_sqs, is_dragging
    if board.is_game_over() or board.turn != human_color:
        return
    is_dragging = True
    sq = xy2sq(event.x, event.y)
    if sq is None:
        return
    piece = board.piece_at(sq)
    if piece is None or piece.color != board.turn:
        return
    from_sq = sq
    avail_sqs = {m.to_square for m in board.legal_moves if m.from_square == sq}
    draw()
    ids = canvas.find_withtag(f"sq{sq}")
    drag_item = ids[-1] if ids else None
    if drag_item:
        canvas.tag_raise(drag_item)

def drag(event):
    if drag_item:
        canvas.coords(drag_item, event.x-SQ//2, event.y-SQ//2)

def end_drag(event):
    global drag_item, from_sq, avail_sqs, last_move, is_dragging
    if not is_dragging:
        click_move(event)
        return
    if drag_item is None:
        return
    to_sq = xy2sq(event.x, event.y)
    if to_sq in avail_sqs:
        move = chess.Move(from_sq, to_sq)
        if move in board.legal_moves:
            board.push(move)
            last_move = move
            # engine reply
            draw()
            make_ai_move()
    drag_item = None
    from_sq  = None
    avail_sqs.clear()
    is_dragging = False
    draw()

def click_move(event):
    global from_sq, avail_sqs, last_move
    if board.is_game_over() or board.turn != human_color:
        return
    sq = xy2sq(event.x, event.y)
    if sq is None:
        return

    if from_sq is None:                          # first click
        piece = board.piece_at(sq)
        if piece is None or piece.color != board.turn:
            return
        from_sq = sq
        avail_sqs = {m.to_square for m in board.legal_moves
                     if m.from_square == sq}
        draw()
    else:                                        # second click
        if sq in avail_sqs:
            move = chess.Move(from_sq, sq)
            if move in board.legal_moves:
                board.push(move)
                last_move = move
                # engine reply
                draw()
                make_ai_move()
        from_sq = None
        avail_sqs.clear()
        draw()

# ──────────────────────────────────────────
# navigation & utility buttons
def previous_move():
    global last_move, undone_moves
    if board.move_stack:
        move = board.pop()
        undone_moves.append(move)
        last_move = board.peek() if board.move_stack else None
        draw()

def next_move():
    global last_move, undone_moves
    if undone_moves:
        move = undone_moves.pop()
        board.push(move)
        last_move = move
        draw()

def new_game():
    global board, last_move, undone_moves, from_sq, avail_sqs, human_color
    board = chess.Board()
    human_color = chess.WHITE if white_bottom else chess.BLACK
    last_move = from_sq = None
    undone_moves = []
    avail_sqs.clear()
    draw()


def flip_board():
    global white_bottom, human_color            # human_color already exists
    white_bottom = not white_bottom
    helpers.white_bottom = white_bottom         # keep helpers in sync

    if not board.move_stack:                    # no moves played yet
        human_color = chess.WHITE if white_bottom else chess.BLACK
        if board.turn != human_color:           # AI now starts
            make_ai_move()

    draw()


# ──────────────────────────────────────────
# event bindings
canvas.bind("<ButtonPress-1>", start_drag)
canvas.bind("<B1-Motion>",      drag)
canvas.bind("<ButtonRelease-1>", end_drag)

nav_frame = tk.Frame(root)
nav_frame.pack(pady=5)

tk.Button(nav_frame, text="◀ Previous", command=previous_move).pack(side=tk.LEFT, padx=2)
tk.Button(nav_frame, text="Next ▶",     command=next_move).pack(side=tk.LEFT, padx=2)
tk.Button(nav_frame, text="New Game",   command=new_game).pack(side=tk.LEFT, padx=2)
tk.Button(nav_frame, text="Flip Board", command=flip_board).pack(side=tk.LEFT, padx=2)

status_label = tk.Label(root, text="White to move", relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# keyboard shortcuts
root.bind("<Left>",  lambda _e: previous_move())
root.bind("<Right>", lambda _e: next_move())
root.bind("<n>",     lambda _e: new_game())
root.bind("<f>",     lambda _e: flip_board())

# start GUI loop
draw()
root.mainloop()
