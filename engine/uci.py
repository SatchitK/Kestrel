import sys, chess, threading, time
from .search import find_best_move

class UciEngine:
    def run(self):
        board = chess.Board()
        while True:
            cmd = sys.stdin.readline().strip()
            if cmd == "uci":
                print("id name Kestrel-Engine")
                print("id author You")
                print("uciok")
            elif cmd.startswith("position"):
                if "startpos" in cmd:
                    board = chess.Board()
                    moves = cmd.split("moves")[1].split() if "moves" in cmd else []
                else:
                    fen, *moves = cmd[9:].split(" moves")
                    board = chess.Board(fen)
                    moves = moves[0].split() if moves else []
                for m in moves:
                    board.push_uci(m)
            elif cmd.startswith("go"):
                tl = 3.0
                if "movetime" in cmd:
                    tl = int(cmd.split("movetime")[1]) / 1000.0
                move = find_best_move(board, tl)
                print(f"bestmove {move.uci()}")
            elif cmd == "isready":
                print("readyok")
            elif cmd == "quit":
                break

if __name__ == "__main__":
    UciEngine().run()
