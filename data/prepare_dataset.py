from pathlib import Path
import sys
import shutil
import chess.pgn
import torch
from engine.utils import board_to_tensor

# Configuration
CHUNK_SIZE = 100000
SRC_DIR = Path("data/raw_pgn")
TMP_DIR = Path("data/tmp_chunks")
OUT_FILE = Path("data/positions.pt")

def save_chunk(buffer, chunk_index):
    if not buffer:
        return chunk_index

    TMP_DIR.mkdir(exist_ok=True)
    chunk_path = TMP_DIR / f"chunk_{chunk_index:04}.pt"
    torch.save(torch.stack(buffer), chunk_path)
    print(f"Saved {len(buffer):,} positions to {chunk_path.name}")
    buffer.clear()
    return chunk_index + 1

def process_pgn_files():
    pgn_files = sorted(SRC_DIR.glob("*.pgn"))
    if not pgn_files:
        sys.exit(f"No PGN files found in {SRC_DIR}. Exiting.")

    buffer = []
    chunk_index = 0
    total_games = 0
    total_positions = 0

    for pgn_file in pgn_files:
        print(f"Processing {pgn_file.name}")
        with pgn_file.open(encoding="utf-8", errors="ignore") as file:
            while True:
                try:
                    game = chess.pgn.read_game(file)
                except Exception as error:
                    print(f"Error reading game: {error}")
                    continue

                if game is None:  # End of file
                    print("Reached end of file.")
                    break

                total_games += 1
                board = game.board()
                for move in game.mainline_moves():
                    buffer.append(board_to_tensor(board))
                    board.push(move)
                    if len(buffer) == CHUNK_SIZE:
                        chunk_index = save_chunk(buffer, chunk_index)

    # Save remaining positions
    chunk_index = save_chunk(buffer, chunk_index)
    if chunk_index == 0:
        sys.exit("No positions extracted from PGN files. Exiting.")

    # Combine all chunks into a single tensor
    print("Combining chunks...")
    tensors = []
    for chunk_file in sorted(TMP_DIR.glob("chunk_*.pt")):
        print(f"Loading {chunk_file.name}")
        tensor = torch.load(chunk_file)
        tensors.append(tensor)
        total_positions += tensor.shape[0]

    final_tensor = torch.cat(tensors)
    torch.save(final_tensor, OUT_FILE)

    # Clean up temporary files
    shutil.rmtree(TMP_DIR)
    print(
        f"Finished processing: {total_games:,} games -> {total_positions:,} positions "
        f"saved to {OUT_FILE}"
    )

def main():
    process_pgn_files()

if __name__ == "__main__":
    main()