import torch
import chess
from engine.utils import board_to_tensor
from engine.model import KestrelModel

def evaluate_board(board: chess.Board, model: KestrelModel, device='cpu'):
    model.eval()
    with torch.no_grad():
        tensor = board_to_tensor(board).unsqueeze(0).to(device)
        policy_logits, value = model(tensor)
        policy = torch.softmax(policy_logits, dim=1)
        return policy.squeeze(0).cpu(), value.item()
