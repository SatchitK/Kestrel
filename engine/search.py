import math
import chess
import numpy as np
import torch
from engine.evaluation import evaluate_board
from engine.utils import board_to_tensor

# --- AlphaZero move encoding (8x8x73 = 4672) ---

QUEEN_DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
KNIGHT_DIRS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

def encode_move_alphazero(move: chess.Move, board: chess.Board) -> int:
    from_square = move.from_square
    to_square = move.to_square
    from_rank = chess.square_rank(from_square)
    from_file = chess.square_file(from_square)
    to_rank = chess.square_rank(to_square)
    to_file = chess.square_file(to_square)
    d_rank = to_rank - from_rank
    d_file = to_file - from_file

    # 1. Queen moves (8 directions, up to 7 squares)
    for dir_idx, (dr, df) in enumerate(QUEEN_DIRS):
        for n in range(1, 8):
            if d_rank == dr * n and d_file == df * n:
                return from_square * 73 + dir_idx * 7 + (n - 1)

    # 2. Knight moves (8 possibilities)
    for knight_idx, (dr, df) in enumerate(KNIGHT_DIRS):
        if d_rank == dr and d_file == df:
            return from_square * 73 + 56 + knight_idx

    # 3. Underpromotions (9 possibilities: 3 directions x 3 pieces)
    if board.piece_at(from_square) and board.piece_at(from_square).piece_type == chess.PAWN:
        if (from_rank == 6 and to_rank == 7) or (from_rank == 1 and to_rank == 0):
            promo_dirs = [(1, 0), (1, -1), (1, 1)] if board.turn == chess.WHITE else [(-1, 0), (-1, -1), (-1, 1)]
            for dir_idx, (dr, df) in enumerate(promo_dirs):
                if d_rank == dr and d_file == df:
                    if move.promotion in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
                        promo_map = {chess.KNIGHT: 0, chess.BISHOP: 1, chess.ROOK: 2}
                        promo_idx = promo_map[move.promotion]
                        return from_square * 73 + 64 + dir_idx * 3 + promo_idx

    return None

def decode_move_alphazero(idx: int, board: chess.Board) -> chess.Move:
    from_square = idx // 73
    rem = idx % 73

    if rem < 56:
        dir_idx = rem // 7
        n = rem % 7 + 1
        dr, df = QUEEN_DIRS[dir_idx]
        from_rank = chess.square_rank(from_square)
        from_file = chess.square_file(from_square)
        to_rank = from_rank + dr * n
        to_file = from_file + df * n
        if 0 <= to_rank < 8 and 0 <= to_file < 8:
            to_square = chess.square(to_file, to_rank)
            piece = board.piece_at(from_square)
            if piece and piece.piece_type == chess.PAWN:
                if (board.turn == chess.WHITE and to_rank == 7) or (board.turn == chess.BLACK and to_rank == 0):
                    return chess.Move(from_square, to_square, promotion=chess.QUEEN)
            return chess.Move(from_square, to_square)

    elif rem < 64:
        knight_idx = rem - 56
        dr, df = KNIGHT_DIRS[knight_idx]
        from_rank = chess.square_rank(from_square)
        from_file = chess.square_file(from_square)
        to_rank = from_rank + dr
        to_file = from_file + df
        if 0 <= to_rank < 8 and 0 <= to_file < 8:
            to_square = chess.square(to_file, to_rank)
            return chess.Move(from_square, to_square)

    else:
        promo_rem = rem - 64
        dir_idx = promo_rem // 3
        promo_idx = promo_rem % 3
        promo_dirs = [(1, 0), (1, -1), (1, 1)] if board.turn == chess.WHITE else [(-1, 0), (-1, -1), (-1, 1)]
        dr, df = promo_dirs[dir_idx]
        from_rank = chess.square_rank(from_square)
        from_file = chess.square_file(from_square)
        to_rank = from_rank + dr
        to_file = from_file + df
        if 0 <= to_rank < 8 and 0 <= to_file < 8:
            to_square = chess.square(to_file, to_rank)
            promo_map = [chess.KNIGHT, chess.BISHOP, chess.ROOK]
            promotion = promo_map[promo_idx]
            return chess.Move(from_square, to_square, promotion=promotion)

    return None

NUM_MOVES = 8 * 8 * 73 # 4672

class Node:
    def __init__(self, parent=None, prior_p=1.0, move=None):
        self.parent = parent
        self.children = {}
        self.visit_count = 0
        self.total_action_value = 0.0
        self.prior_p = prior_p
        self.move = move

    def expand(self, board, policy):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return
        legal_indices = []
        move_map = {}
        for move in legal_moves:
            idx = encode_move_alphazero(move, board)
            if idx is not None and 0 <= idx < NUM_MOVES:
                legal_indices.append(idx)
                move_map[move] = idx

        if isinstance(policy, torch.Tensor):
            policy = policy.detach().cpu().numpy()

        masked_policy = np.zeros_like(policy)
        masked_policy[legal_indices] = policy[legal_indices]

        if masked_policy.sum() > 0:
            masked_policy /= masked_policy.sum()
        else:
            masked_policy[legal_indices] = 1.0 / len(legal_indices)

        for move, idx in move_map.items():
            prior = masked_policy[idx]
            self.children[move] = Node(parent=self, prior_p=prior, move=move)

    def select_child(self, c_puct=1.0):
        best_score = -float('inf')
        best_child = None
        for move, child in self.children.items():
            score = child.ucb_score(c_puct)
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    def ucb_score(self, c_puct):
        q_value = self.total_action_value / self.visit_count if self.visit_count > 0 else 0
        uct_score = q_value + c_puct * self.prior_p * (math.sqrt(self.parent.visit_count) / (1 + self.visit_count))
        return uct_score

    def backpropagate(self, value):
        self.visit_count += 1
        self.total_action_value += value
        if self.parent:
            self.parent.backpropagate(-value)

class MCTS:
    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.root = None

    def search(self, board, simulations_number):
        self.root = Node()
        policy, value = evaluate_board(board, self.model, self.device)
        self.root.expand(board, policy)

        for _ in range(simulations_number):
            node = self.root
            search_board = board.copy()

            # --- Repetition/stagnation check ---
            if search_board.is_repetition(3) or search_board.is_fifty_moves():
                value = 0.0
                node.backpropagate(value)
                continue

            while node.children:
                node = node.select_child()
                if node is None:
                    break
                search_board.push(node.move)

                if search_board.is_repetition(3) or search_board.is_fifty_moves():
                    value = 0.0
                    node.backpropagate(value)
                    break

            if node is None:
                continue

            if not search_board.is_game_over():
                policy, value = evaluate_board(search_board, self.model, self.device)
                node.expand(search_board, policy)
            else:
                if search_board.is_checkmate():
                    value = -1.0
                else:
                    value = 0.0

            node.backpropagate(value)

        if not self.root.children:
            return None

        legal_moves = list(board.legal_moves)
        best_move = None
        max_visits = -1
        for move in legal_moves:
            child = self.root.children.get(move, None)
            if child and child.visit_count > max_visits:
                max_visits = child.visit_count
                best_move = move

        return best_move

def find_best_move(board, model, simulations=400, device='cpu'):
    mcts = MCTS(model, device=device)
    return mcts.search(board, simulations)

def should_extend_search(board, move):
    """Determine if search should be extended"""
    board.push(move)
    extend = False

    # Extend if in check
    if board.is_check():
        extend = True

    # Extend for captures
    if move.capture:
        extend = True

    # Extend for promotions
    if move.promotion:
        extend = True

    board.pop()
    return extend

def is_blunder(board, move, model, device='cpu', threshold=-2.0):
    """Check if a move is a potential blunder"""
    board.push(move)

    # Quick evaluation after the move
    input_tensor = board_to_tensor(board).unsqueeze(0).to(device)
    with torch.no_grad():
        _, value = model(input_tensor)

    position_eval = value.item()
    board.pop()

    # If position evaluation drops significantly, it might be a blunder
    return position_eval < threshold
