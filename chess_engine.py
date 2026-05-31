"""
Chess engine: board state, move generation, and game logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import copy

# Piece constants
EMPTY = 0
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
WHITE, BLACK = 1, -1

PIECE_NAMES = {PAWN: 'P', KNIGHT: 'N', BISHOP: 'B', ROOK: 'R', QUEEN: 'Q', KING: 'K'}


@dataclass
class Piece:
    kind: int
    color: int

    def __repr__(self):
        name = PIECE_NAMES.get(self.kind, '?')
        return name if self.color == WHITE else name.lower()


@dataclass
class Move:
    from_sq: tuple[int, int]
    to_sq: tuple[int, int]
    promotion: Optional[int] = None
    is_castling: bool = False
    is_en_passant: bool = False
    captured: Optional[Piece] = None

    def __hash__(self):
        return hash((self.from_sq, self.to_sq, self.promotion))

    def __eq__(self, other):
        return (self.from_sq == other.from_sq and
                self.to_sq == other.to_sq and
                self.promotion == other.promotion)


class Board:
    def __init__(self):
        self.grid: list[list[Optional[Piece]]] = [[None] * 8 for _ in range(8)]
        self.turn = WHITE
        self.castling_rights = {
            WHITE: {'kingside': True, 'queenside': True},
            BLACK: {'kingside': True, 'queenside': True},
        }
        self.en_passant_target: Optional[tuple[int, int]] = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.move_history: list[Move] = []
        self._setup()

    def _setup(self):
        back_rank = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for col, kind in enumerate(back_rank):
            self.grid[0][col] = Piece(kind, WHITE)
            self.grid[7][col] = Piece(kind, BLACK)
        for col in range(8):
            self.grid[1][col] = Piece(PAWN, WHITE)
            self.grid[6][col] = Piece(PAWN, BLACK)

    def get(self, row: int, col: int) -> Optional[Piece]:
        if 0 <= row < 8 and 0 <= col < 8:
            return self.grid[row][col]
        return None

    def clone(self) -> 'Board':
        b = Board.__new__(Board)
        b.grid = [[self.grid[r][c] for c in range(8)] for r in range(8)]
        b.turn = self.turn
        b.castling_rights = {
            WHITE: dict(self.castling_rights[WHITE]),
            BLACK: dict(self.castling_rights[BLACK]),
        }
        b.en_passant_target = self.en_passant_target
        b.halfmove_clock = self.halfmove_clock
        b.fullmove_number = self.fullmove_number
        b.move_history = list(self.move_history)
        return b

    # ── move application ──────────────────────────────────────────────────────

    def apply_move(self, move: Move) -> None:
        r1, c1 = move.from_sq
        r2, c2 = move.to_sq
        piece = self.grid[r1][c1]
        move.captured = self.grid[r2][c2]

        # En passant capture
        if move.is_en_passant:
            ep_row = r2 - piece.color
            move.captured = self.grid[ep_row][c2]
            self.grid[ep_row][c2] = None

        # Castling – move the rook
        if move.is_castling:
            if c2 > c1:  # kingside
                self.grid[r1][5] = self.grid[r1][7]
                self.grid[r1][7] = None
            else:         # queenside
                self.grid[r1][3] = self.grid[r1][0]
                self.grid[r1][0] = None

        # Place piece
        self.grid[r2][c2] = Piece(move.promotion or piece.kind, piece.color) if move.promotion else piece
        self.grid[r1][c1] = None

        # Update castling rights
        if piece.kind == KING:
            self.castling_rights[piece.color]['kingside'] = False
            self.castling_rights[piece.color]['queenside'] = False
        if piece.kind == ROOK:
            if c1 == 7:
                self.castling_rights[piece.color]['kingside'] = False
            if c1 == 0:
                self.castling_rights[piece.color]['queenside'] = False
        # If a rook is captured, revoke that right too
        if move.captured and move.captured.kind == ROOK:
            opp = move.captured.color
            if c2 == 7:
                self.castling_rights[opp]['kingside'] = False
            if c2 == 0:
                self.castling_rights[opp]['queenside'] = False

        # En passant target
        if piece.kind == PAWN and abs(r2 - r1) == 2:
            self.en_passant_target = ((r1 + r2) // 2, c1)
        else:
            self.en_passant_target = None

        # Clocks
        if piece.kind == PAWN or move.captured:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        if self.turn == BLACK:
            self.fullmove_number += 1

        self.turn = -self.turn
        self.move_history.append(move)

    # ── move generation ───────────────────────────────────────────────────────

    def legal_moves(self, color: Optional[int] = None) -> list[Move]:
        color = color or self.turn
        moves = []
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.color == color:
                    moves.extend(self._piece_moves(r, c, p))
        return [m for m in moves if not self._leaves_king_in_check(m, color)]

    def legal_moves_from(self, row: int, col: int) -> list[Move]:
        p = self.grid[row][col]
        if not p:
            return []
        raw = self._piece_moves(row, col, p)
        return [m for m in raw if not self._leaves_king_in_check(m, p.color)]

    def _piece_moves(self, r: int, c: int, p: Piece) -> list[Move]:
        if p.kind == PAWN:   return self._pawn_moves(r, c, p)
        if p.kind == KNIGHT: return self._knight_moves(r, c, p)
        if p.kind == BISHOP: return self._slider_moves(r, c, p, [(1,1),(1,-1),(-1,1),(-1,-1)])
        if p.kind == ROOK:   return self._slider_moves(r, c, p, [(1,0),(-1,0),(0,1),(0,-1)])
        if p.kind == QUEEN:  return self._slider_moves(r, c, p,
            [(1,1),(1,-1),(-1,1),(-1,-1),(1,0),(-1,0),(0,1),(0,-1)])
        if p.kind == KING:   return self._king_moves(r, c, p)
        return []

    def _pawn_moves(self, r: int, c: int, p: Piece) -> list[Move]:
        moves = []
        d = p.color  # WHITE=+1, BLACK=-1 from row 0 at white's back rank
        start_row = 1 if p.color == WHITE else 6
        promo_row = 7 if p.color == WHITE else 0

        def add(r2, c2, **kw):
            if r2 == promo_row:
                for promo in [QUEEN, ROOK, BISHOP, KNIGHT]:
                    moves.append(Move((r, c), (r2, c2), promotion=promo, **kw))
            else:
                moves.append(Move((r, c), (r2, c2), **kw))

        # Forward
        if self.get(r + d, c) is None:
            add(r + d, c)
            if r == start_row and self.get(r + 2*d, c) is None:
                add(r + 2*d, c)

        # Captures
        for dc in (-1, 1):
            nr, nc = r + d, c + dc
            target = self.get(nr, nc)
            if target and target.color != p.color:
                add(nr, nc)
            elif (nr, nc) == self.en_passant_target:
                add(nr, nc, is_en_passant=True)

        return moves

    def _knight_moves(self, r: int, c: int, p: Piece) -> list[Move]:
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = r+dr, c+dc
            target = self.get(nr, nc)
            if target is None or target.color != p.color:
                if 0 <= nr < 8 and 0 <= nc < 8:
                    moves.append(Move((r, c), (nr, nc)))
        return moves

    def _slider_moves(self, r: int, c: int, p: Piece, dirs: list) -> list[Move]:
        moves = []
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                target = self.grid[nr][nc]
                if target is None:
                    moves.append(Move((r, c), (nr, nc)))
                elif target.color != p.color:
                    moves.append(Move((r, c), (nr, nc)))
                    break
                else:
                    break
                nr += dr
                nc += dc
        return moves

    def _king_moves(self, r: int, c: int, p: Piece) -> list[Move]:
        moves = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r+dr, c+dc
                target = self.get(nr, nc)
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if target is None or target.color != p.color:
                        moves.append(Move((r, c), (nr, nc)))

        # Castling
        rights = self.castling_rights[p.color]
        if rights['kingside'] and self._can_castle(r, c, p.color, kingside=True):
            moves.append(Move((r, c), (r, c+2), is_castling=True))
        if rights['queenside'] and self._can_castle(r, c, p.color, kingside=False):
            moves.append(Move((r, c), (r, c-2), is_castling=True))
        return moves

    def _can_castle(self, r: int, c: int, color: int, kingside: bool) -> bool:
        cols = [5, 6] if kingside else [1, 2, 3]
        rook_col = 7 if kingside else 0
        rook = self.get(r, rook_col)
        if not rook or rook.kind != ROOK or rook.color != color:
            return False
        for nc in cols:
            if nc in (5, 6) if kingside else nc in (1, 2, 3):
                if self.grid[r][nc] is not None:
                    return False
        # King cannot pass through or land in check
        check_cols = [c, c+1, c+2] if kingside else [c, c-1, c-2]
        for nc in check_cols:
            if self._square_attacked(r, nc, -color):
                return False
        return True

    def _leaves_king_in_check(self, move: Move, color: int) -> bool:
        b = self.clone()
        b.apply_move(move)
        return b._king_in_check(color)

    def _king_in_check(self, color: int) -> bool:
        kr, kc = self._king_pos(color)
        if kr is None:
            return True
        return self._square_attacked(kr, kc, -color)

    def _king_pos(self, color: int) -> tuple[Optional[int], Optional[int]]:
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.kind == KING and p.color == color:
                    return r, c
        return None, None

    def _square_attacked(self, row: int, col: int, by_color: int) -> bool:
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.color == by_color:
                    if p.kind == KING:
                        # Check adjacency directly — never call _king_moves here,
                        # as that would recurse through _can_castle → _square_attacked.
                        if abs(r - row) <= 1 and abs(c - col) <= 1 and (r, c) != (row, col):
                            return True
                    else:
                        for m in self._piece_moves(r, c, p):
                            if m.to_sq == (row, col):
                                return True
        return False

    # ── game status ───────────────────────────────────────────────────────────

    def is_check(self) -> bool:
        return self._king_in_check(self.turn)

    def is_checkmate(self) -> bool:
        return self.is_check() and len(self.legal_moves()) == 0

    def is_stalemate(self) -> bool:
        return not self.is_check() and len(self.legal_moves()) == 0

    def is_draw_by_50(self) -> bool:
        return self.halfmove_clock >= 100

    def game_over(self) -> Optional[str]:
        if self.is_checkmate():
            winner = 'White' if self.turn == BLACK else 'Black'
            return f'Checkmate! {winner} wins!'
        if self.is_stalemate():
            return 'Stalemate! Draw!'
        if self.is_draw_by_50():
            return 'Draw by 50-move rule!'
        return None
