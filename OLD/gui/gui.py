import tkinter as tk
import chess
import pathlib
import torch
import torch.nn.functional as F
from engine.model import KestrelModel  # Updated import
from engine.utils import board_to_tensor
from engine.search import find_best_move as get_best_move # Import MCTS search
from gui.gui_constants import NUM_SQ as SQ, LIGHT_SQ_COLOR as LIGHT, DARK_SQ_COLOR as DARK, WHITE_BOTTOM as white_bottom
from gui.gui_helpers import sq2xy, xy2sq

root = tk.Tk()
root.title("Kestrel")

logo = tk.PhotoImage(file="assets/kestrel_icon_logo.png")
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
last_move = None
is_dragging = False
undone_moves = []

# Load the AI model (updated for KestrelModel)
# Replace the existing model loading section with:
MODEL_WEIGHTS_PATH = pathlib.Path("model_weights/kestrel_epoch_1.pth")  # Updated path
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

try:
    model = KestrelModel(num_residual_blocks=12).to(DEVICE)  # Match your pretrained model
    if MODEL_WEIGHTS_PATH.exists():
        model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location=DEVICE))
        model.eval()
        print(f"Model loaded from {MODEL_WEIGHTS_PATH}")
    else:
        print(f"Warning: Model file {MODEL_WEIGHTS_PATH} not found. Using untrained model.")
        model = None
except Exception as e:
    print(f"Error loading model: {e}")
    model = None


# AI settings
USE_MCTS = True  # Set to False for simpler evaluation
MCTS_SIMULATIONS = 400  # Reduced for faster response
AI_THINKING = False  # Track if AI is thinking

def draw():
    canvas.delete("all")
    for r in range(8):
        for c in range(8):
            color = LIGHT if (r + c) % 2 == 0 else DARK
            x = c*SQ if white_bottom else (7-c)*SQ
            y = r*SQ if white_bottom else (7-r)*SQ
            canvas.create_rectangle(x, y, x+SQ, y+SQ, fill=color, width=0)
    
    # Highlight last move
    if last_move:
        for sq in [last_move.from_square, last_move.to_square]:
            x, y = sq2xy(sq)
            canvas.create_rectangle(x, y, x+SQ, y+SQ, fill="#f6f669", stipple="gray50")
    
    # Highlight check
    if board.is_check():
        king_square = board.king(board.turn)
        if king_square is not None:
            x, y = sq2xy(king_square)
            canvas.create_rectangle(x, y, x+SQ, y+SQ, fill="#ff4d4d", stipple="gray50")
    
    # Draw pieces
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            x, y = sq2xy(sq)
            key = ('w' if piece.color else 'b') + piece.symbol().upper()
            canvas.create_image(x, y, anchor="nw", image=IMG[key], tags=f"sq{sq}")
    
    # Draw available moves
    for sq in avail_sqs:
        x, y = sq2xy(sq)
        cx, cy = x + SQ//2, y + SQ//2
        rdot = SQ // 6
        canvas.create_oval(cx-rdot, cy-rdot, cx+rdot, cy+rdot, fill="#4da6ff", outline="")
    
    # Show game status
    update_status()

def update_status():
    """Update the status bar with game information"""
    status_text = ""
    if board.is_checkmate():
        winner = "White" if board.turn == chess.BLACK else "Black"
        status_text = f"Checkmate! {winner} wins!"
    elif board.is_stalemate():
        status_text = "Stalemate! Draw."
    elif board.is_insufficient_material():
        status_text = "Insufficient material! Draw."
    elif board.is_check():
        status_text = "Check!"
    elif AI_THINKING:
        status_text = "AI is thinking..."
    else:
        status_text = f"{'White' if board.turn == chess.WHITE else 'Black'} to move"
    
    status_label.config(text=status_text)

def start_drag(event):
    global drag_item, from_sq, avail_sqs, is_dragging
    if AI_THINKING or board.is_game_over():
        return
    
    is_dragging = True
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
    if drag_item and not AI_THINKING:
        canvas.coords(drag_item, event.x-SQ//2, event.y-SQ//2)

def end_drag(event):
    global drag_item, from_sq, avail_sqs, last_move, is_dragging
    if AI_THINKING:
        return
    
    if not is_dragging:
        click_move(event)
        return
    
    if drag_item is None:
        return
    
    to_sq = xy2sq(event.x, event.y)
    if to_sq is not None and to_sq in avail_sqs:
        move = chess.Move(from_sq, to_sq)
        # Handle pawn promotion
        if move in board.legal_moves:
            board.push(move)
            last_move = move
            root.after(100, ai_move)  # Delay AI move slightly for better UX
    
    drag_item = None
    from_sq = None
    avail_sqs = set()
    is_dragging = False
    draw()

def click_move(event):
    global from_sq, avail_sqs, last_move
    if AI_THINKING or board.is_game_over():
        return
    
    sq = xy2sq(event.x, event.y)
    if sq is None:
        return
    
    if from_sq is None:
        piece = board.piece_at(sq)
        if piece is None or piece.color != board.turn:
            return
        from_sq = sq
        avail_sqs = {move.to_square for move in board.legal_moves if move.from_square == sq}
        draw()
    else:
        if sq in avail_sqs:
            move = chess.Move(from_sq, sq)
            if move in board.legal_moves:
                board.push(move)
                last_move = move
                root.after(100, ai_move)  # Delay AI move slightly
        from_sq = None
        avail_sqs = set()
        draw()

def ai_move():
    global last_move, AI_THINKING
    
    if board.is_game_over():
        return
    
    if model is None:
        print("No model loaded, using random moves")
        import random
        legal_moves = list(board.legal_moves)
        if legal_moves:
            best_move = random.choice(legal_moves)
            board.push(best_move)
            last_move = best_move
        return
    
    AI_THINKING = True
    draw()
    
    try:
        if USE_MCTS:
            # Use MCTS search - update parameter order to match search.py
            best_move = get_best_move(board, model, simulations=MCTS_SIMULATIONS, device=DEVICE)
        else:
            # Simple evaluation-based move selection
            best_move = simple_ai_move()
        
        if best_move and best_move in board.legal_moves:
            board.push(best_move)
            last_move = best_move
    except Exception as e:
        print(f"AI Error: {e}")
        # Fallback to random move
        import random
        legal_moves = list(board.legal_moves)
        if legal_moves:
            best_move = random.choice(legal_moves)
            board.push(best_move)
            last_move = best_move
    
    AI_THINKING = False
    draw()

def simple_ai_move():
    """Simple evaluation-based move selection (fallback)"""
    if model is None:
        return None
        
    legal_moves = list(board.legal_moves)
    best_move = None
    best_score = float("-inf")
    
    for move in legal_moves:
        board.push(move)
        input_tensor = board_to_tensor(board).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            policy_logits, value = model(input_tensor)
        
        # Use value for position evaluation
        score = value.item()
        
        # Adjust score based on turn (negate for opponent)
        if board.turn == chess.BLACK:
            score = -score
        
        if score > best_score:
            best_score = score
            best_move = move
        
        board.pop()
    
    return best_move


def enhanced_simple_ai_move():
    """Enhanced evaluation with tactical awareness"""
    if model is None:
        return None
        
    legal_moves = list(board.legal_moves)
    best_move = None
    best_score = float("-inf")
    
    for move in legal_moves:
        board.push(move)
        
        # Check if this move leads to immediate tactical threats
        if board.is_check():
            # Penalize moves that put us in check
            score = -10.0
        else:
            input_tensor = board_to_tensor(board).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                policy_logits, value = model(input_tensor)
            score = value.item()
            
            # Add material safety check
            if is_piece_hanging(board):
                score -= 5.0  # Penalize hanging pieces
        
        if board.turn == chess.BLACK:
            score = -score
            
        if score > best_score:
            best_score = score
            best_move = move
            
        board.pop()
    
    return best_move

def is_piece_hanging(board):
    """Check if any pieces are hanging (undefended and under attack)"""
    hanging_pieces = []
    
    # Check all pieces of the current player
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == board.turn:
            # Check if this piece is under attack
            if board.is_attacked_by(not board.turn, square):
                # Check if the piece is defended
                if not board.is_attacked_by(board.turn, square):
                    hanging_pieces.append(square)
                else:
                    # Even if defended, check if the exchange is unfavorable
                    attackers = get_attackers_value(board, square, not board.turn)
                    defenders = get_attackers_value(board, square, board.turn)
                    piece_value = get_piece_value(piece.piece_type)
                    
                    if attackers and min(attackers) < piece_value:
                        hanging_pieces.append(square)
    
    return len(hanging_pieces) > 0

def get_piece_value(piece_type):
    """Get the value of a piece type"""
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0  # King can't really be "hanging"
    }
    return values.get(piece_type, 0)

def get_attackers_value(board, square, color):
    """Get values of all pieces attacking a square"""
    attackers = []
    for attacker_square in chess.SQUARES:
        piece = board.piece_at(attacker_square)
        if piece and piece.color == color:
            if board.is_attacked_by(color, square):
                # Check if this specific piece can attack the square
                temp_board = board.copy()
                temp_board.remove_piece_at(attacker_square)
                if not temp_board.is_attacked_by(color, square):
                    attackers.append(get_piece_value(piece.piece_type))
    return attackers



def previous_move():
    global last_move, undone_moves
    if AI_THINKING:
        return
    
    if board.move_stack:
        move = board.pop()
        undone_moves.append(move)
        last_move = board.peek() if board.move_stack else None
        draw()

def next_move():
    global last_move, undone_moves
    if AI_THINKING:
        return
    
    if undone_moves:
        move = undone_moves.pop()
        board.push(move)
        last_move = move
        draw()

def new_game():
    global board, last_move, undone_moves, from_sq, avail_sqs
    if AI_THINKING:
        return
    
    board = chess.Board()
    last_move = None
    undone_moves = []
    from_sq = None
    avail_sqs = set()
    draw()

def flip_board():
    global white_bottom
    if AI_THINKING:
        return
    
    white_bottom = not white_bottom
    draw()

def toggle_mcts():
    global USE_MCTS
    USE_MCTS = not USE_MCTS
    mcts_button.config(text=f"MCTS: {'ON' if USE_MCTS else 'OFF'}")

# Event bindings
canvas.bind("<Button-1>", start_drag)
canvas.bind("<B1-Motion>", drag)
canvas.bind("<ButtonRelease-1>", end_drag)

# Navigation frame
nav_frame = tk.Frame(root)
nav_frame.pack(pady=5)

tk.Button(nav_frame, text="◀ Previous", command=previous_move).pack(side=tk.LEFT, padx=2)
tk.Button(nav_frame, text="Next ▶", command=next_move).pack(side=tk.LEFT, padx=2)
tk.Button(nav_frame, text="New Game", command=new_game).pack(side=tk.LEFT, padx=2)
tk.Button(nav_frame, text="Flip Board", command=flip_board).pack(side=tk.LEFT, padx=2)

# AI controls frame
ai_frame = tk.Frame(root)
ai_frame.pack(pady=5)

mcts_button = tk.Button(ai_frame, text=f"MCTS: {'ON' if USE_MCTS else 'OFF'}", command=toggle_mcts)
mcts_button.pack(side=tk.LEFT, padx=2)

# Status bar
status_label = tk.Label(root, text="White to move", relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# Keyboard shortcuts
root.bind("<Left>", lambda event: previous_move())
root.bind("<Right>", lambda event: next_move())
root.bind("<n>", lambda event: new_game())
root.bind("<f>", lambda event: flip_board())

# Start the game
draw()
root.mainloop()

