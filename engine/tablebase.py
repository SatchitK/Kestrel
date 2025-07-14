"""
engine/tablebase.py – thin Syzygy wrapper
Copy all *.rtbw / *.rtbz files (3–5 pieces) into engine/syzygy/
"""

from pathlib import Path
import chess, chess.syzygy

# ──────────────────────────────────────────────
# initialisation
# ──────────────────────────────────────────────
_TB = chess.syzygy.open_tablebase(
    Path(__file__).with_suffix("").parent / "syzygy"
)

# ──────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────
def in_tb(b: chess.Board) -> bool:
    """True iff position is contained in the local TBs."""
    return chess.popcount(b.occupied) <= 7

def tb_wdl(b: chess.Board) -> int | None:
    """
    Syzygy WDL score from the *side-to-move* view:
    +2  win,  +1  draw+,  0  draw  –1  draw–,  –2  loss
    Returns None when the position is not in TB.
    """
    if not in_tb(b):
        return None
    stripped = b.copy()
    stripped.castling_rights = 0
    try:
        return _TB.probe_wdl(stripped)
    except chess.syzygy.MissingTableError:
        return None

def tb_centi(b: chess.Board) -> int | None:
    """
    Map WDL to a centipawn score large enough to override any
    heuristic evaluation but small enough to stay inside ±INF.
    """
    wdl = tb_wdl(b)
    if wdl is None:
        return None
    return {+2:  32000,
            +1:   1000,
             0:      0,
            -1:  -1000,
            -2: -32000}[wdl]

def tb_best(b: chess.Board):
    """
    Return the *exact* best move according to Syzygy
    or None when the position is not in TB.
    """
    if not in_tb(b):
        return None
    stripped = b.copy()
    stripped.castling_rights = 0
    best, best_wdl = None, -3
    for mv in stripped.legal_moves:
        stripped.push(mv)
        try:
            wdl = _TB.probe_wdl(stripped)
        except chess.syzygy.MissingTableError:
            wdl = -3
        stripped.pop()
        if wdl > best_wdl:
            best, best_wdl = mv, wdl
    return best
