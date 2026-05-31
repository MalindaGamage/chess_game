"""
Render chess pieces using pure pygame drawing (no external images needed).
"""

import pygame
from chess_engine import PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, WHITE, BLACK

# Color palette
WHITE_PIECE   = (255, 252, 240)
WHITE_OUTLINE = (180, 160, 120)
BLACK_PIECE   = ( 40,  35,  30)
BLACK_OUTLINE = ( 90,  75,  55)
GOLD          = (212, 175,  55)


def _draw_circle(surf, color, cx, cy, r, outline=None, width=2):
    pygame.draw.circle(surf, color, (cx, cy), r)
    if outline:
        pygame.draw.circle(surf, outline, (cx, cy), r, width)


def draw_piece(surf: pygame.Surface, kind: int, color: int, x: int, y: int, size: int) -> None:
    """Draw a chess piece centred at (x, y) within a cell of `size` pixels."""
    fc = WHITE_PIECE if color == WHITE else BLACK_PIECE
    oc = WHITE_OUTLINE if color == WHITE else BLACK_OUTLINE
    s = size // 2  # half-cell scale reference

    def p(rx, ry):
        return (int(x + rx * s), int(y + ry * s))

    def circle(rx, ry, r, fc=fc, oc=oc, w=2):
        _draw_circle(surf, fc, int(x + rx * s), int(y + ry * s), int(r * s), oc, w)

    def poly(pts, fc=fc, oc=oc):
        mapped = [p(rx, ry) for rx, ry in pts]
        pygame.draw.polygon(surf, fc, mapped)
        pygame.draw.polygon(surf, oc, mapped, 2)

    if kind == PAWN:
        # Base
        poly([(-0.55, 0.85), (0.55, 0.85), (0.4, 0.65), (-0.4, 0.65)])
        # Stem
        poly([(-0.2, 0.65), (0.2, 0.65), (0.15, 0.1), (-0.15, 0.1)])
        # Head
        circle(0, -0.1, 0.28)

    elif kind == KNIGHT:
        # Base
        poly([(-0.55, 0.85), (0.55, 0.85), (0.45, 0.65), (-0.45, 0.65)])
        # Body
        pts = [(-0.35, 0.65), (0.35, 0.65), (0.35, 0.0), (0.1, -0.3),
               (0.3, -0.65), (-0.0, -0.75), (-0.25, -0.55), (-0.35, -0.1)]
        poly(pts)
        # Ear
        poly([(0.05, -0.55), (0.3, -0.65), (0.1, -0.35)])
        # Eye
        ex, ey = int(x + 0.1 * s), int(y - 0.35 * s)
        pygame.draw.circle(surf, GOLD, (ex, ey), max(2, int(0.06 * s)))

    elif kind == BISHOP:
        # Base
        poly([(-0.55, 0.85), (0.55, 0.85), (0.4, 0.65), (-0.4, 0.65)])
        # Body
        poly([(-0.25, 0.65), (0.25, 0.65), (0.15, 0.05), (-0.15, 0.05)])
        # Head
        circle(0, -0.15, 0.3)
        # Cross
        pygame.draw.line(surf, oc, p(0, -0.48), p(0, 0.1), 2)
        pygame.draw.line(surf, oc, p(-0.15, -0.25), p(0.15, -0.25), 2)
        # Ball top
        circle(0, -0.52, 0.07)

    elif kind == ROOK:
        # Base
        poly([(-0.55, 0.85), (0.55, 0.85), (0.45, 0.65), (-0.45, 0.65)])
        # Shaft
        poly([(-0.3, 0.65), (0.3, 0.65), (0.3, -0.3), (-0.3, -0.3)])
        # Battlements
        for dx in [-0.28, 0.0, 0.28]:
            poly([(dx - 0.12, -0.3), (dx + 0.12, -0.3),
                  (dx + 0.12, -0.65), (dx - 0.12, -0.65)])

    elif kind == QUEEN:
        # Base
        poly([(-0.6, 0.85), (0.6, 0.85), (0.45, 0.65), (-0.45, 0.65)])
        # Body
        pts = [(-0.35, 0.65), (0.35, 0.65), (0.3, 0.1), (0.1, -0.2),
               (0.0, -0.55), (-0.1, -0.2), (-0.3, 0.1)]
        poly(pts)
        # Crown balls
        for bx in [-0.35, -0.15, 0.0, 0.15, 0.35]:
            circle(bx, -0.62, 0.08)
        # Centre jewel
        circle(0, -0.55, 0.1, fc=GOLD, oc=oc)

    elif kind == KING:
        # Base
        poly([(-0.6, 0.85), (0.6, 0.85), (0.45, 0.65), (-0.45, 0.65)])
        # Body
        poly([(-0.3, 0.65), (0.3, 0.65), (0.3, -0.1), (-0.3, -0.1)])
        # Head
        circle(0, -0.25, 0.3)
        # Cross
        pygame.draw.line(surf, GOLD, p(0, -0.65), p(0, -0.1), 3)
        pygame.draw.line(surf, GOLD, p(-0.2, -0.5), p(0.2, -0.5), 3)
