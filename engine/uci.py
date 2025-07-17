import sys, chess, threading, time
from .search import find_best_move

class UciEngine:
    def __init__(self):
        self.search_thread = None
        self.stop_search = False

    def run(self):
        board = chess.Board()
        while True:
            cmd = sys.stdin.readline().strip()
            if cmd == "uci":
                print("id name Kestrel-Engine-Improved", flush=True)
                print("id author You", flush=True)
                print("uciok", flush=True)
            elif cmd.startswith("position"):
                if "startpos" in cmd:
                    board = chess.Board()
                    moves = cmd.split("moves")[1].split() if "moves" in cmd else []
                else:
                    fen, *moves_part = cmd[9:].split(" moves")
                    board = chess.Board(fen)
                    moves = moves_part[0].split() if moves_part else []
                for m in moves:
                    board.push_uci(m)
            elif cmd.startswith("go"):
                tl = 3.0
                infinite = False
                if "movetime" in cmd:
                    tl = int(cmd.split("movetime")[1]) / 1000.0
                elif "infinite" in cmd:
                    infinite = True
                    tl = float('inf')
                # Improved: Run search in thread for interruptibility
                self.stop_search = False
                self.search_thread = threading.Thread(target=self._search, args=(board, tl))
                self.search_thread.start()
                if not infinite:
                    time.sleep(tl)
                    self.stop_search = True
                    self.search_thread.join()
            elif cmd == "stop":
                self.stop_search = True
                if self.search_thread:
                    self.search_thread.join()
            elif cmd == "isready":
                print("readyok", flush=True)
            elif cmd == "quit":
                break

    def _search(self, board, tl):
        move = find_best_move(board, tl)
        if not self.stop_search:
            print(f"bestmove {move.uci()}", flush=True)

if __name__ == "__main__":
    UciEngine().run()
