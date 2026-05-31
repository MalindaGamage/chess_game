"""
Chess game – animated pygame UI.
Controls:
  Click a piece → highlight legal moves
  Click a highlighted square → make the move
  R  – restart
  U  – undo last two half-moves (take back)
  1/2/3 – AI difficulty (1=easy, 2=medium, 3=hard)
  F  – flip board
  Q  – quit
"""

import sys, threading
import pygame
from chess_engine import (Board, Move, WHITE, BLACK,
                           PAWN, KNIGHT, BISHOP, ROOK, QUEEN)
from assets import draw_piece
from ai_player import best_move

# ── constants ─────────────────────────────────────────────────────────────────

FPS          = 60
CELL         = 90           # px per square
SIDEBAR      = 240
WIDTH        = CELL * 8 + SIDEBAR
HEIGHT       = CELL * 8 + 60   # +60 for status bar
ANIM_FRAMES  = 14           # frames for piece glide animation

# Board colours
LIGHT        = (240, 217, 181)
DARK         = (181, 136,  99)
HIGHLIGHT    = (100, 200, 100, 160)   # legal-move dot
SELECTED_CLR = (255, 255,  80, 120)   # selected piece overlay
LAST_MOVE_LT = (205, 210, 106, 180)
LAST_MOVE_DK = (170, 162,  58, 180)
CHECK_CLR    = (220,  50,  50, 160)
SIDEBAR_BG   = ( 30,  30,  40)
TEXT_CLR     = (220, 220, 220)
ACCENT       = (212, 175,  55)
BTN_CLR      = ( 60,  60,  80)
BTN_HOVER    = ( 90,  90, 120)
SHADOW       = (  0,   0,   0, 80)

# ── helpers ───────────────────────────────────────────────────────────────────

def sq_to_px(row: int, col: int, flipped: bool) -> tuple[int, int]:
    """Centre of a board square in screen pixels."""
    r = (7 - row) if flipped else row
    c = (7 - col) if flipped else col
    return (c * CELL + CELL // 2, r * CELL + CELL // 2)


def px_to_sq(mx: int, my: int, flipped: bool) -> tuple[int, int] | None:
    if mx >= CELL * 8 or my >= CELL * 8:
        return None
    col_idx = mx // CELL
    row_idx = my // CELL
    if flipped:
        return (7 - row_idx, 7 - col_idx)
    return (row_idx, col_idx)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3

# ── animation state ───────────────────────────────────────────────────────────

class AnimPiece:
    def __init__(self, kind, color, sx, sy, ex, ey, frames):
        self.kind   = kind
        self.color  = color
        self.sx, self.sy = sx, sy
        self.ex, self.ey = ex, ey
        self.frames = frames
        self.elapsed = 0
        self.done   = False

    def tick(self):
        self.elapsed += 1
        if self.elapsed >= self.frames:
            self.done = True

    @property
    def pos(self):
        t = ease_out(min(self.elapsed / self.frames, 1.0))
        return (int(lerp(self.sx, self.ex, t)),
                int(lerp(self.sy, self.ey, t)))

# ── particle effect ───────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color):
        import random
        self.x   = x + random.randint(-10, 10)
        self.y   = y + random.randint(-10, 10)
        self.vx  = random.uniform(-3, 3)
        self.vy  = random.uniform(-5, -1)
        self.life = random.randint(20, 40)
        self.color = color
        self.r   = random.randint(3, 7)

    def tick(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = max(0, int(255 * self.life / 40))
        s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.r, self.r), self.r)
        surf.blit(s, (int(self.x - self.r), int(self.y - self.r)))

# ── promotion dialog ──────────────────────────────────────────────────────────

def promotion_dialog(screen, flipped, row, col, color, font):
    pieces = [QUEEN, ROOK, BISHOP, KNIGHT]
    cx, cy = sq_to_px(row, col, flipped)
    boxes  = []
    for i, kind in enumerate(pieces):
        bx = cx - CELL*2 + i * CELL
        by = cy - CELL // 2
        boxes.append((pygame.Rect(bx, by, CELL, CELL), kind))

    # Dim overlay
    overlay = pygame.Surface((CELL*8, CELL*8), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    while True:
        screen.blit(overlay, (0, 0))
        for rect, kind in boxes:
            pygame.draw.rect(screen, (60, 55, 70), rect, border_radius=8)
            pygame.draw.rect(screen, ACCENT, rect, 2, border_radius=8)
            draw_piece(screen, kind, color, rect.centerx, rect.centery, CELL)

        lbl = font.render('Promote to:', True, TEXT_CLR)
        screen.blit(lbl, (boxes[0][0].x, boxes[0][0].y - 28))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, kind in boxes:
                    if rect.collidepoint(event.pos):
                        return kind

# ── main game class ───────────────────────────────────────────────────────────

class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('♟  Python Chess')
        self.clock  = pygame.time.Clock()

        self.font_lg  = pygame.font.SysFont('segoeui', 20, bold=True)
        self.font_md  = pygame.font.SysFont('segoeui', 16)
        self.font_sm  = pygame.font.SysFont('segoeui', 13)
        self.font_ttl = pygame.font.SysFont('segoeui', 26, bold=True)

        self.board      = Board()
        self.selected   = None         # (row, col)
        self.legal_here : list[Move] = []
        self.flipped    = False        # board orientation
        self.ai_color   = BLACK        # AI plays Black by default
        self.ai_depth   = 3           # difficulty
        self.ai_thinking = False
        self.ai_result  : Move | None = None
        self.anim       : AnimPiece | None = None
        self.particles  : list[Particle] = []
        self.status_msg = 'White to move'
        self.captured_white : list = []  # pieces captured by Black (from White)
        self.captured_black : list = []  # pieces captured by White (from Black)
        self.move_log   : list[str] = []

        self._build_buttons()

    # ── sidebar buttons ───────────────────────────────────────────────────────

    def _build_buttons(self):
        bx = CELL * 8 + 20
        self.buttons = [
            {'label': 'New Game  [R]', 'key': pygame.K_r,  'rect': pygame.Rect(bx, 350, 200, 36), 'action': self._restart},
            {'label': 'Undo  [U]',     'key': pygame.K_u,  'rect': pygame.Rect(bx, 396, 200, 36), 'action': self._undo},
            {'label': 'Flip Board  [F]','key': pygame.K_f, 'rect': pygame.Rect(bx, 442, 200, 36), 'action': self._flip},
            {'label': 'Easy  [1]',     'key': pygame.K_1,  'rect': pygame.Rect(bx, 504, 95, 36),  'action': lambda: self._set_diff(2)},
            {'label': 'Med  [2]',      'key': pygame.K_2,  'rect': pygame.Rect(bx+105, 504, 95, 36),'action': lambda: self._set_diff(3)},
            {'label': 'Hard  [3]',     'key': pygame.K_3,  'rect': pygame.Rect(bx, 550, 200, 36), 'action': lambda: self._set_diff(4)},
            {'label': 'Play White',    'key': None,         'rect': pygame.Rect(bx, 606, 95, 36),  'action': lambda: self._set_side(BLACK)},
            {'label': 'Play Black',    'key': None,         'rect': pygame.Rect(bx+105, 606, 95, 36),'action': lambda: self._set_side(WHITE)},
        ]

    # ── actions ───────────────────────────────────────────────────────────────

    def _restart(self):
        self.board    = Board()
        self.selected = None
        self.legal_here = []
        self.anim     = None
        self.particles = []
        self.captured_white = []
        self.captured_black = []
        self.move_log  = []
        self.ai_thinking = False
        self.ai_result = None
        self._update_status()

    def _undo(self):
        if len(self.board.move_history) < 2:
            return
        b = Board()
        history = list(self.board.move_history[:-2])
        self._restart()
        for mv in history:
            self.board.apply_move(mv)
            # maintain capture lists
            if mv.captured:
                lst = self.captured_black if mv.captured.color == BLACK else self.captured_white
                lst.append(mv.captured.kind)
        self._update_status()

    def _flip(self):
        self.flipped = not self.flipped

    def _set_diff(self, d):
        self.ai_depth = d
        names = {2:'Easy', 3:'Medium', 4:'Hard'}
        self.status_msg = f'AI difficulty: {names.get(d, d)}'

    def _set_side(self, ai_color):
        self.ai_color = ai_color
        self._restart()

    def _update_status(self):
        result = self.board.game_over()
        if result:
            self.status_msg = result
        elif self.board.is_check():
            who = 'White' if self.board.turn == WHITE else 'Black'
            self.status_msg = f'{who} is in CHECK!'
        else:
            who = 'White' if self.board.turn == WHITE else 'Black'
            self.status_msg = f'{who} to move'

    # ── AI thread ─────────────────────────────────────────────────────────────

    def _run_ai(self):
        move = best_move(self.board.clone(), depth=self.ai_depth)
        self.ai_result = move
        self.ai_thinking = False

    def _trigger_ai(self):
        if (self.board.turn == self.ai_color and
                not self.board.game_over() and
                not self.ai_thinking):
            self.ai_thinking = True
            t = threading.Thread(target=self._run_ai, daemon=True)
            t.start()

    # ── move execution ────────────────────────────────────────────────────────

    def _execute_move(self, move: Move):
        piece = self.board.grid[move.from_sq[0]][move.from_sq[1]]
        sx, sy = sq_to_px(*move.from_sq, self.flipped)
        ex, ey = sq_to_px(*move.to_sq,   self.flipped)

        # Promotion check for human moves
        if (piece.kind == PAWN and
                move.promotion is None and
                piece.color != self.ai_color and
                (move.to_sq[0] == 7 or move.to_sq[0] == 0)):
            move.promotion = promotion_dialog(
                self.screen, self.flipped, *move.to_sq, piece.color, self.font_md)

        # Track captures for display
        target = self.board.grid[move.to_sq[0]][move.to_sq[1]]
        if target:
            lst = self.captured_black if target.color == BLACK else self.captured_white
            lst.append(target.kind)
            self._spawn_particles(ex, ey, target.color)

        # Move log
        files = 'abcdefgh'
        fr, fc = move.from_sq
        tr, tc = move.to_sq
        notation = f'{files[fc]}{fr+1}→{files[tc]}{tr+1}'
        who = 'W' if piece.color == WHITE else 'B'
        self.move_log.append(f'{who}: {notation}')

        self.board.apply_move(move)
        self.selected   = None
        self.legal_here = []
        self._update_status()

        # Kick off animation
        self.anim = AnimPiece(piece.kind, piece.color, sx, sy, ex, ey, ANIM_FRAMES)
        self._trigger_ai()

    def _spawn_particles(self, x, y, color):
        clr = (240, 220, 180) if color == WHITE else (80, 60, 40)
        for _ in range(20):
            self.particles.append(Particle(x, y, clr))

    # ── input handling ────────────────────────────────────────────────────────

    def _handle_click(self, mx, my):
        if self.anim and not self.anim.done:
            return
        if self.board.game_over():
            return
        if self.board.turn == self.ai_color:
            return

        sq = px_to_sq(mx, my, self.flipped)
        if sq is None:
            return
        row, col = sq
        piece = self.board.grid[row][col]

        if self.selected:
            # Try to complete a move
            for mv in self.legal_here:
                if mv.to_sq == (row, col):
                    self._execute_move(mv)
                    return
            # Re-select if same colour
            self.selected   = None
            self.legal_here = []

        if piece and piece.color == self.board.turn:
            self.selected   = (row, col)
            self.legal_here = self.board.legal_moves_from(row, col)

    # ── drawing ───────────────────────────────────────────────────────────────

    def _draw_board(self):
        last_move = self.board.move_history[-1] if self.board.move_history else None
        kr, kc = None, None
        if self.board.is_check():
            kr, kc = self.board._king_pos(self.board.turn)

        for r in range(8):
            for c in range(8):
                # Screen coords of top-left corner
                sr = (7 - r) if self.flipped else r
                sc = (7 - c) if self.flipped else c
                x, y = sc * CELL, sr * CELL
                rect = pygame.Rect(x, y, CELL, CELL)

                # Base colour
                base = LIGHT if (r + c) % 2 == 0 else DARK
                pygame.draw.rect(self.screen, base, rect)

                # Last-move highlight
                if last_move and ((r, c) == last_move.from_sq or (r, c) == last_move.to_sq):
                    hl = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                    hl.fill(LAST_MOVE_LT if (r + c) % 2 == 0 else LAST_MOVE_DK)
                    self.screen.blit(hl, (x, y))

                # Check highlight
                if (r, c) == (kr, kc):
                    hl = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                    hl.fill(CHECK_CLR)
                    self.screen.blit(hl, (x, y))

                # Selected square
                if self.selected == (r, c):
                    hl = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                    hl.fill(SELECTED_CLR)
                    self.screen.blit(hl, (x, y))

                # Legal-move dots
                cx, cy = x + CELL//2, y + CELL//2
                for mv in self.legal_here:
                    if mv.to_sq == (r, c):
                        dot_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                        if self.board.grid[r][c]:
                            # Capture ring
                            pygame.draw.circle(dot_surf, HIGHLIGHT, (CELL//2, CELL//2), CELL//2 - 4, 5)
                        else:
                            pygame.draw.circle(dot_surf, HIGHLIGHT, (CELL//2, CELL//2), 13)
                        self.screen.blit(dot_surf, (x, y))
                        break

        # Rank/file labels
        for i in range(8):
            num = str(i + 1) if not self.flipped else str(8 - i)
            lbl = self.font_sm.render(num, True, DARK if i % 2 == 0 else LIGHT)
            self.screen.blit(lbl, (2, i * CELL + 2))
            letter = 'abcdefgh'[i] if not self.flipped else 'hgfedcba'[i]
            lbl = self.font_sm.render(letter, True, DARK if i % 2 == 0 else LIGHT)
            self.screen.blit(lbl, (i * CELL + CELL - 12, CELL * 8 - 16))

    def _draw_pieces(self):
        animating_sq = (
            (self.anim.ex, self.anim.ey) if (self.anim and not self.anim.done) else None
        )
        anim_from = (
            self.board.move_history[-1].from_sq if (self.anim and self.board.move_history) else None
        )

        for r in range(8):
            for c in range(8):
                p = self.board.grid[r][c]
                if not p:
                    continue
                cx, cy = sq_to_px(r, c, self.flipped)
                # Skip the piece at its destination while animating
                if (self.anim and not self.anim.done and
                        (r, c) == self.board.move_history[-1].to_sq):
                    continue
                draw_piece(self.screen, p.kind, p.color, cx, cy, CELL)

        # Draw animated piece on top
        if self.anim and not self.anim.done:
            px_, py_ = self.anim.pos
            # Shadow
            shad = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            pygame.draw.ellipse(shad, SHADOW, (10, CELL//2+10, CELL-20, 20))
            self.screen.blit(shad, (px_ - CELL//2, py_ - CELL//2))
            draw_piece(self.screen, self.anim.kind, self.anim.color, px_, py_, CELL)

    def _draw_sidebar(self):
        bx = CELL * 8
        pygame.draw.rect(self.screen, SIDEBAR_BG, (bx, 0, SIDEBAR, HEIGHT))

        # Title
        title = self.font_ttl.render('Python Chess', True, ACCENT)
        self.screen.blit(title, (bx + 20, 18))

        # Turn indicator (glowing circle)
        turn_color = (255, 252, 240) if self.board.turn == WHITE else (40, 35, 30)
        ring_color = ACCENT
        pygame.draw.circle(self.screen, ring_color, (bx + 30, 65), 14)
        pygame.draw.circle(self.screen, turn_color, (bx + 30, 65), 11)
        who = 'White' if self.board.turn == WHITE else 'Black'
        lbl = self.font_md.render(f"{who}'s turn", True, TEXT_CLR)
        self.screen.blit(lbl, (bx + 50, 57))

        # Difficulty
        diff_names = {2:'Easy', 3:'Medium', 4:'Hard'}
        dlbl = self.font_sm.render(f"Difficulty: {diff_names.get(self.ai_depth,'?')}", True, (160,160,160))
        self.screen.blit(dlbl, (bx + 20, 92))

        # AI thinking indicator
        if self.ai_thinking:
            dots = '.' * ((pygame.time.get_ticks() // 400) % 4)
            albl = self.font_md.render(f'AI thinking{dots}', True, (150, 200, 255))
            self.screen.blit(albl, (bx + 20, 115))

        # Captured pieces
        y = 145
        for i, (label, lst, color) in enumerate([
            ('Captured by White:', self.captured_black, BLACK),
            ('Captured by Black:', self.captured_white, WHITE),
        ]):
            lbl = self.font_sm.render(label, True, (160, 160, 160))
            self.screen.blit(lbl, (bx + 20, y))
            y += 18
            for j, kind in enumerate(lst[:16]):
                px_ = bx + 20 + (j % 8) * 24 + 12
                py_ = y + (j // 8) * 24 + 12
                draw_piece(self.screen, kind, color, px_, py_, 22)
            y += (len(lst[:16]) // 8 + 1) * 24 + 6

        # Move log
        log_y = 220
        lbl = self.font_sm.render('Move Log', True, (160, 160, 160))
        self.screen.blit(lbl, (bx + 20, log_y))
        for i, entry in enumerate(self.move_log[-8:]):
            c = (200, 200, 200) if i % 2 == 0 else (160, 160, 160)
            el = self.font_sm.render(entry, True, c)
            self.screen.blit(el, (bx + 20, log_y + 16 + i * 14))

        # Buttons
        mx, my = pygame.mouse.get_pos()
        for btn in self.buttons:
            hover = btn['rect'].collidepoint(mx, my)
            pygame.draw.rect(self.screen, BTN_HOVER if hover else BTN_CLR,
                             btn['rect'], border_radius=6)
            pygame.draw.rect(self.screen, ACCENT, btn['rect'], 1, border_radius=6)
            txt = self.font_sm.render(btn['label'], True, TEXT_CLR)
            tx  = btn['rect'].x + (btn['rect'].width - txt.get_width()) // 2
            ty  = btn['rect'].y + (btn['rect'].height - txt.get_height()) // 2
            self.screen.blit(txt, (tx, ty))

    def _draw_status_bar(self):
        pygame.draw.rect(self.screen, (20, 20, 28),
                         (0, CELL * 8, CELL * 8, 60))
        result = self.board.game_over()
        msg = result or self.status_msg
        color = ACCENT if result else TEXT_CLR
        lbl = self.font_lg.render(msg, True, color)
        self.screen.blit(lbl, (CELL * 8 // 2 - lbl.get_width() // 2,
                                CELL * 8 + 18))

    def _draw_particles(self):
        for p in self.particles:
            p.draw(self.screen)

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        self._trigger_ai()

        while True:
            dt = self.clock.tick(FPS)

            # ── events ─────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    for btn in self.buttons:
                        if btn['key'] == event.key:
                            btn['action']()
                    if event.key == pygame.K_q:
                        pygame.quit(); sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.buttons:
                        if btn['rect'].collidepoint(event.pos):
                            btn['action']()
                            break
                    else:
                        self._handle_click(*event.pos)

            # ── AI result ──────────────────────────────────────────────────
            if self.ai_result is not None:
                move = self.ai_result
                self.ai_result = None
                if not self.board.game_over():
                    self._execute_move(move)

            # ── animation tick ─────────────────────────────────────────────
            if self.anim and not self.anim.done:
                self.anim.tick()

            # ── particle tick ──────────────────────────────────────────────
            for p in self.particles:
                p.tick()
            self.particles = [p for p in self.particles if p.life > 0]

            # ── render ─────────────────────────────────────────────────────
            self.screen.fill((15, 15, 20))
            self._draw_board()
            self._draw_pieces()
            self._draw_particles()
            self._draw_sidebar()
            self._draw_status_bar()
            pygame.display.flip()


if __name__ == '__main__':
    ChessGame().run()
