"""
Simple AI opponent using minimax with alpha-beta pruning.
"""

from chess_engine import Board, Move, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
import random

PIECE_VALUES = {PAWN: 100, KNIGHT: 320, BISHOP: 330, ROOK: 500, QUEEN: 900, KING: 20000}

# Positional bonus tables (from White's perspective, row 0 = rank 1)
PAWN_TABLE = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [ 5,  5, 10, 25, 25, 10,  5,  5],
    [ 0,  0,  0, 20, 20,  0,  0,  0],
    [ 5, -5,-10,  0,  0,-10, -5,  5],
    [ 5, 10, 10,-20,-20, 10, 10,  5],
    [ 0,  0,  0,  0,  0,  0,  0,  0],
]
KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50],
]
BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20],
]
ROOK_TABLE = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [ 0,  0,  0,  5,  5,  0,  0,  0],
]
QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20],
]
KING_MIDDLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20],
]

PIECE_TABLES = {
    PAWN: PAWN_TABLE, KNIGHT: KNIGHT_TABLE, BISHOP: BISHOP_TABLE,
    ROOK: ROOK_TABLE, QUEEN: QUEEN_TABLE, KING: KING_MIDDLE,
}


def _table_score(kind: int, row: int, col: int, color: int) -> int:
    table = PIECE_TABLES.get(kind)
    if not table:
        return 0
    # White reads table top-down (row 7 is back rank), Black mirrors
    r = row if color == WHITE else 7 - row
    return table[7 - r][col]  # table index 0 = rank 8 visually


def evaluate(board: Board) -> int:
    """Static evaluation in centipawns from White's perspective."""
    score = 0
    for r in range(8):
        for c in range(8):
            p = board.grid[r][c]
            if p:
                val = PIECE_VALUES[p.kind] + _table_score(p.kind, r, c, p.color)
                score += val * p.color  # WHITE=+1, BLACK=-1
    return score


def minimax(board: Board, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
    result = board.game_over()
    if result:
        if 'White wins' in result:
            return 100000
        if 'Black wins' in result:
            return -100000
        return 0

    if depth == 0:
        return evaluate(board)

    moves = board.legal_moves()
    if not moves:
        return evaluate(board)

    # Move ordering: captures first
    moves.sort(key=lambda m: (m.captured is not None), reverse=True)

    if maximizing:
        best = -999999
        for move in moves:
            nb = board.clone()
            nb.apply_move(move)
            val = minimax(nb, depth - 1, alpha, beta, False)
            best = max(best, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best
    else:
        best = 999999
        for move in moves:
            nb = board.clone()
            nb.apply_move(move)
            val = minimax(nb, depth - 1, alpha, beta, True)
            best = min(best, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best


def best_move(board: Board, depth: int = 3) -> Move | None:
    moves = board.legal_moves()
    if not moves:
        return None

    moves.sort(key=lambda m: (m.captured is not None), reverse=True)

    best_val = 999999 if board.turn == BLACK else -999999
    best_mv = None
    alpha, beta = -999999, 999999

    for move in moves:
        nb = board.clone()
        nb.apply_move(move)
        val = minimax(nb, depth - 1, alpha, beta, board.turn == BLACK)
        if board.turn == BLACK:
            if val < best_val:
                best_val = val
                best_mv = move
            beta = min(beta, val)
        else:
            if val > best_val:
                best_val = val
                best_mv = move
            alpha = max(alpha, val)

    return best_mv
