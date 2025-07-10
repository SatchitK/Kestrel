import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
from engine.model import KestrelModel
from engine.utils import board_to_tensor
import chess.pgn
from tqdm import tqdm
import numpy as np

# Configuration
DATASET_PATH = Path("data/raw_pgn/ccrl.pgn")
PROCESSED_DATASET_PATH = Path("data/processed/positions.pt")
MODEL_WEIGHTS_DIR = Path("model_weights")
MODEL_WEIGHTS_DIR.mkdir(exist_ok=True)

BATCH_SIZE = 32  # Reduced due to larger model
EPOCHS = 10
LEARNING_RATE = 0.001
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_GAMES = 10000

class ChessDataset(Dataset):
    def __init__(self, processed_file=None, pgn_file=None, max_games=None):
        self.positions = []
        self.values = []
        
        if processed_file and Path(processed_file).exists():
            print(f"Loading preprocessed dataset from {processed_file}...")
            data = torch.load(processed_file)
            if isinstance(data, dict) and "positions" in data and "values" in data:
                # Ensure positions are float32 tensors
                self.positions = [pos.to(dtype=torch.float32) for pos in data["positions"]]
                # Ensure values are float32
                self.values = torch.tensor(data["values"], dtype=torch.float32)
            else:
                raise ValueError(f"Invalid format in preprocessed file: {processed_file}")
        elif pgn_file:
            print("Preprocessing dataset...")
            with open(pgn_file, "r", encoding="utf-8", errors="ignore") as file:
                for i, game in enumerate(tqdm(iter(lambda: chess.pgn.read_game(file), None), desc="Parsing PGN Games")):
                    if max_games is not None and i >= max_games:
                        break
                    
                    board = game.board()
                    result = game.headers["Result"]
                    target_value = self._parse_result(result)
                    
                    # Extract positions from the game
                    for move in game.mainline_moves():
                        self.positions.append(board_to_tensor(board))
                        # Ensure target_value is float32
                        self.values.append(float(target_value))
                        board.push(move)
            
            print(f"Loaded {len(self.positions)} positions from {pgn_file} (max_games={max_games})")
            
            # Convert values to tensor immediately to ensure dtype consistency
            self.values = torch.tensor(self.values, dtype=torch.float32)
            
            if processed_file:
                print(f"Saving preprocessed dataset to {processed_file}...")
                Path(processed_file).parent.mkdir(parents=True, exist_ok=True)
                torch.save({"positions": self.positions, "values": self.values}, processed_file)
        else:
            raise ValueError("Either processed_file or pgn_file must be provided.")

    def __len__(self):
        return len(self.positions)

    def __getitem__(self, idx):
        # Ensure both position and value are float32
        position = self.positions[idx].to(dtype=torch.float32)
        value = self.values[idx].to(dtype=torch.float32)
        return position, value

    def _parse_result(self, result):
        if result == "1-0":
            return 1.0  # Win
        elif result == "0-1":
            return -1.0  # Loss
        else:
            return 0.0  # Draw


def train():
    print("Using device:", DEVICE)
    
    # Load dataset
    dataset = ChessDataset(
        processed_file=PROCESSED_DATASET_PATH,
        pgn_file=DATASET_PATH,
        max_games=MAX_GAMES
    )
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # Initialize model
    model = KestrelModel(num_residual_blocks=8).to(DEVICE)
    
    # Loss functions
    value_criterion = nn.MSELoss()
    
    # Optimizer
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    
    # Training loop
    for epoch in range(EPOCHS):
        model.train()
        epoch_value_loss = 0
        total_batches = 0
        
        print(f"Epoch {epoch + 1}/{EPOCHS}")
        
        with tqdm(total=len(dataloader), desc=f"Training Epoch {epoch + 1}") as pbar:
            for batch in dataloader:
                boards, target_values = batch
                boards = boards.to(DEVICE)
                target_values = target_values.to(DEVICE).unsqueeze(1)
                
                optimizer.zero_grad()
                
                # Forward pass
                policy_logits, predicted_values = model(boards)
                
                # Only train on value for now (no policy labels available)
                value_loss = value_criterion(predicted_values, target_values)
                
                # Backward pass
                value_loss.backward()
                optimizer.step()
                
                epoch_value_loss += value_loss.item()
                total_batches += 1
                
                pbar.set_postfix({
                    "Value Loss": f"{value_loss.item():.4f}",
                })
                pbar.update(1)
        
        avg_value_loss = epoch_value_loss / total_batches
        print(f"Epoch {epoch + 1} - Value Loss: {avg_value_loss:.4f}")
        
        # Save model
        torch.save(model.state_dict(), MODEL_WEIGHTS_DIR / f"kestrel_epoch_{epoch + 1}.pth")

if __name__ == "__main__":
    train()
