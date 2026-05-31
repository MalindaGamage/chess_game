"""
Chess 3D Perspective – pure pygame, no ursina.
Real perspective projection: board and pieces in 3D.

Controls:
  Left-click           – select / move piece
  A / D or Left/Right  – rotate camera left/right
  W / S or Up/Down     – tilt camera up/down
  Scroll or +/-        – zoom in/out
  R – new game   U – undo   F – flip   1/2/3 – difficulty   Q – quit
"""

import pygame, sys, math, threading
sys.path.insert(0, r'e:\chess_game')
from chess_engine import Board, Move, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING
from ai_player import best_move

# ─── Screen ───────────────────────────────────────────────────────────────────
W, H = 1280, 720
FPS  = 60

# ─── Camera ──────────────────────────────────────────────────────────────────
_azim = math.radians(20)    # horizontal orbit (A/D)
_elev = math.radians(35)    # elevation  (W/S)
_dist = 22.0                # zoom
FOV   = 520                 # perspective focal length (px)

# ─── Colors ───────────────────────────────────────────────────────────────────
BG       = (14, 11, 24)
SQ_LIGHT = (240, 217, 181)
SQ_DARK  = (181, 136,  99)
SQ_LT_DK = (200, 180, 148)  # shaded side of light square
SQ_DK_DK = (140, 100,  70)  # shaded side of dark square
W_PIECE  = (255, 252, 240)
B_PIECE  = ( 38,  30,  22)
W_SHADE  = (200, 195, 175)
B_SHADE  = ( 22,  17,  12)
GOLD     = (212, 175,  55)
GOLD_DK  = (160, 130,  35)
WOOD_T   = (140,  90,  38)
WOOD_S   = ( 90,  58,  22)
WOOD_BOT = ( 65,  42,  16)
HL_MOV   = ( 60, 200,  60)
HL_SEL   = (220, 200,  30)
HL_LAST  = (185, 200,  55)
HL_CHK   = (210,  35,  35)
TEXT_CLR = (225, 225, 235)
ACCENT   = (212, 175,  55)
SIDEBAR  = ( 22,  20,  35)

# ─── Perspective projection ───────────────────────────────────────────────────
def _view_basis():
    """Camera position and orthonormal basis (right, up, forward)."""
    ex = _dist * math.sin(_azim) * math.cos(_elev)
    ey = _dist * math.sin(_elev)
    ez = _dist * math.cos(_azim) * math.cos(_elev)
    fl = math.sqrt(ex*ex + ey*ey + ez*ez)
    # Forward = toward origin
    fx, fy, fz = -ex/fl, -ey/fl, -ez/fl
    # Right = forward × world_up  (world_up = Y axis)
    rlen = math.sqrt(fz*fz + fx*fx)
    if rlen < 1e-9:
        rx, ry, rz = 1.0, 0.0, 0.0
    else:
        rx, ry, rz = -fz/rlen, 0.0, fx/rlen
    # Up = right × forward
    ux = ry*fz - rz*fy
    uy = rz*fx - rx*fz
    uz = rx*fy - ry*fx
    return (ex,ey,ez), (rx,ry,rz), (ux,uy,uz), (fx,fy,fz)

def project(px, py, pz):
    """World point → screen (x,y). Returns None if behind camera."""
    (ex,ey,ez),(rx,ry,rz),(ux,uy,uz),(fx,fy,fz) = _view_basis()
    tx, ty, tz = px-ex, py-ey, pz-ez
    cx = rx*tx + ry*ty + rz*tz
    cy = ux*tx + uy*ty + uz*tz
    cz = fx*tx + fy*ty + fz*tz
    if cz <= 0.05:
        return None
    return (W//2 + FOV*cx/cz, H//2 - FOV*cy/cz)

def project_depth(px, py, pz):
    """Returns (screen_pt, depth) or (None, inf)."""
    (ex,ey,ez),(rx,ry,rz),(ux,uy,uz),(fx,fy,fz) = _view_basis()
    tx, ty, tz = px-ex, py-ey, pz-ez
    cx = rx*tx + ry*ty + rz*tz
    cy = ux*tx + uy*ty + uz*tz
    cz = fx*tx + fy*ty + fz*tz
    if cz <= 0.05:
        return None, float('inf')
    return (W//2 + FOV*cx/cz, H//2 - FOV*cy/cz), cz

# ─── Board coordinate helpers ─────────────────────────────────────────────────
_flipped = False

def sq_center(r, c):
    """World-space center of board square surface."""
    if _flipped: r, c = 7-r, 7-c
    return (c - 3.5, 0.0, 3.5 - r)

def sq_corners(r, c, y=0.0):
    """Four 3D corners of square (r,c) at height y.
    Board is centered at origin: x ∈ [-4,4], z ∈ [-4,4]."""
    if _flipped: r, c = 7-r, 7-c
    x0, x1 = c - 4, c - 3
    z0, z1 = 4 - r, 3 - r
    return [(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)]

def point_in_quad(mx, my, corners_2d):
    """Test if screen point (mx,my) is inside a projected quadrilateral."""
    pts = [(int(p[0]), int(p[1])) for p in corners_2d]
    n = len(pts)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > my) != (yj > my)) and \
           (mx < (xj - xi) * (my - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside

# ─── Drawing helpers ──────────────────────────────────────────────────────────
def draw_poly(surf, color, pts_3d, y_offset=0):
    """Project list of 3D points and draw filled polygon."""
    screen_pts = []
    for (x,y,z) in pts_3d:
        p = project(x, y+y_offset, z)
        if p: screen_pts.append(p)
    if len(screen_pts) >= 3:
        pygame.draw.polygon(surf, color, [(int(a),int(b)) for a,b in screen_pts])

def draw_disc(surf, color, cx, cy, cz, radius, n=10):
    """Draw a horizontal disc (circle in XZ plane) in perspective."""
    pts = []
    for i in range(n):
        a = 2*math.pi*i/n
        p = project(cx + radius*math.cos(a), cy, cz + radius*math.sin(a))
        if p: pts.append(p)
    if len(pts) >= 3:
        pygame.draw.polygon(surf, color, [(int(x),int(y)) for x,y in pts])

def draw_cylinder(surf, top_clr, side_clr, cx, cz, y_bot, y_top, r_bot, r_top, n=10):
    """Draw a cylinder section (or frustum) in perspective."""
    # Side faces (draw quads back-to-front sorted by angle from camera)
    (ex,ey,ez),_,_,_ = _view_basis()
    cam_ang = math.atan2(ex - cx, ez - cz)  # camera angle relative to piece

    segs = []
    for i in range(n):
        a0 = 2*math.pi*i/n
        a1 = 2*math.pi*(i+1)/n
        a_mid = (a0+a1)/2
        # Depth of this face segment (use its midpoint)
        mx3 = cx + (r_bot+r_top)/2 * math.cos(a_mid)
        mz3 = cz + (r_bot+r_top)/2 * math.sin(a_mid)
        _, depth = project_depth(mx3, (y_bot+y_top)/2, mz3)

        # Face visibility: only draw faces not facing away from camera
        # Normal of this side face (pointing outward in XZ)
        nx, nz = math.cos(a_mid), math.sin(a_mid)
        # Camera direction from piece
        cdx, cdz = ex-cx, ez-cz
        vis = cdx*nx + cdz*nz  # dot product
        if vis > 0:  # facing camera
            segs.append((depth, a0, a1, r_bot, r_top))

    # Sort far-to-near
    segs.sort(key=lambda s: -s[0])

    for (depth, a0, a1, rb, rt) in segs:
        b0 = project(cx+rb*math.cos(a0), y_bot, cz+rb*math.sin(a0))
        b1 = project(cx+rb*math.cos(a1), y_bot, cz+rb*math.sin(a1))
        t0 = project(cx+rt*math.cos(a0), y_top, cz+rt*math.sin(a0))
        t1 = project(cx+rt*math.cos(a1), y_top, cz+rt*math.sin(a1))
        if all(p is not None for p in [b0,b1,t0,t1]):
            pts = [(int(x),int(y)) for x,y in [b0,b1,t1,t0]]
            pygame.draw.polygon(surf, side_clr, pts)

    # Top disc
    draw_disc(surf, top_clr, cx, y_top, cz, r_top, n)

def draw_sphere_proj(surf, color, shade, cx, cy, cz, radius):
    """Draw a projected sphere (as ellipse with shading)."""
    p = project(cx, cy, cz)
    if p is None: return
    # Approximate screen radius
    p2 = project(cx+radius, cy, cz)
    if p2 is None: return
    sr = max(3, int(abs(p2[0]-p[0])))
    # Draw shadow-side ellipse then bright ellipse
    pygame.draw.ellipse(surf, shade, (int(p[0])-sr, int(p[1])-int(sr*0.6),
                                      sr*2, int(sr*1.2)))
    # Main circle with gradient effect (use smaller bright circle offset up-left)
    pygame.draw.ellipse(surf, color, (int(p[0])-sr+1, int(p[1])-sr+1,
                                      sr*2-2, sr*2-2))
    # Highlight
    hl_r = max(2, sr//3)
    hl = tuple(min(255, c+80) for c in color)
    pygame.draw.circle(surf, hl, (int(p[0])-sr//3, int(p[1])-sr//3), hl_r)

# ─── Piece drawing ────────────────────────────────────────────────────────────
def draw_piece(surf, kind, side, r, c):
    cx, _, cz = sq_center(r, c)
    tc = W_PIECE if side==WHITE else B_PIECE
    sc = W_SHADE if side==WHITE else B_SHADE

    def cyl(yb, yt, rb, rt=None):
        draw_cylinder(surf, tc, sc, cx, cz, yb, yt, rb, rb if rt is None else rt)

    def sph(y, rad):
        draw_sphere_proj(surf, tc, sc, cx, y, cz, rad)

    def gold_disc(y, r):
        draw_cylinder(surf, GOLD, GOLD_DK, cx, cz, y-0.02, y, r, r)

    if kind == PAWN:
        cyl(0.0, 0.12, 0.34)          # base
        cyl(0.12, 0.48, 0.11)         # stem
        sph(0.65, 0.20)               # head

    elif kind == KNIGHT:
        cyl(0.0, 0.12, 0.34)
        cyl(0.12, 0.42, 0.14)
        # Horse head as sphere + cube-ish block
        sph(0.65, 0.22)
        # Snout: small disc pushed forward
        fwd_x = cx + 0.15*math.cos(_azim+math.pi)
        fwd_z = cz + 0.15*math.sin(_azim+math.pi)
        draw_sphere_proj(surf, tc, sc, fwd_x, 0.60, fwd_z, 0.12)
        # Eye dot
        eye_p = project(cx+0.12, 0.67, cz-0.12)
        if eye_p:
            pygame.draw.circle(surf, GOLD, (int(eye_p[0]),int(eye_p[1])), 3)

    elif kind == BISHOP:
        cyl(0.0, 0.12, 0.34)
        cyl(0.12, 0.20, 0.20, 0.20)  # collar ring
        cyl(0.20, 0.75, 0.11)
        sph(0.88, 0.17)
        sph(1.08, 0.08)              # mitre tip
        # gold ball
        p = project(cx, 1.22, cz)
        if p: pygame.draw.circle(surf, GOLD, (int(p[0]),int(p[1])), 4)

    elif kind == ROOK:
        cyl(0.0, 0.12, 0.34)
        cyl(0.12, 0.20, 0.22, 0.22)
        cyl(0.20, 0.72, 0.19)
        cyl(0.72, 0.80, 0.26, 0.26)  # top platform
        # Battlements
        for ang in [0, math.pi/2, math.pi, 3*math.pi/2]:
            bx = cx + 0.17*math.cos(ang)
            bz = cz + 0.17*math.sin(ang)
            draw_cylinder(surf, tc, sc, bx, bz, 0.80, 1.00, 0.07, 0.07)

    elif kind == QUEEN:
        cyl(0.0, 0.12, 0.36)
        cyl(0.12, 0.20, 0.22)
        cyl(0.20, 0.72, 0.12)
        sph(0.88, 0.19)
        gold_disc(1.04, 0.24)        # crown ring
        for i in range(5):
            a = i * 2*math.pi/5
            bx = cx + 0.22*math.cos(a)
            bz = cz + 0.22*math.sin(a)
            p = project(bx, 1.12, bz)
            if p:
                clr = GOLD if i%2==0 else tc
                pygame.draw.circle(surf, clr, (int(p[0]),int(p[1])), 5)

    elif kind == KING:
        cyl(0.0, 0.12, 0.36)
        cyl(0.12, 0.20, 0.22)
        cyl(0.20, 0.80, 0.14)
        sph(0.96, 0.18)
        # Cross
        for y1,y2,r_ in [(1.10,1.42,0.05),(1.24,1.26,0.18)]:
            draw_cylinder(surf, GOLD, GOLD_DK, cx, cz, y1, y2, r_, r_)

# ─── Render list (painter's algorithm) ────────────────────────────────────────
def render_scene(surf, board, selected, leg_sq, highlights):
    """Draw board + pieces sorted back-to-front by depth."""
    B  = 4.0   # half board size (squares go from -4 to +4)
    FR = 4.5   # half frame outer size (0.5 unit wooden border)
    FY = -0.25 # frame bottom y

    # ── Phase 1: Frame (always drawn first, never sorted) ──────────────────
    # Frame top border (wooden surround visible outside the 8x8 squares)
    draw_poly(surf, WOOD_T, [(-FR,0, FR),(FR,0, FR),(FR,0,-FR),(-FR,0,-FR)])

    # Determine which frame sides face the camera (skip back-facing sides)
    (ex,ey,ez),_,_,_ = _view_basis()
    frame_sides = [
        # (face_normal_x, face_normal_z, pts)
        ( 0, 1, [(-FR,FY, FR),(-FR,0, FR),(FR,0, FR),(FR,FY, FR)]),   # front  z=+FR
        ( 0,-1, [(-FR,FY,-FR),(-FR,0,-FR),(FR,0,-FR),(FR,FY,-FR)]),   # back   z=-FR
        ( 1, 0, [(FR,FY,-FR),(FR,0,-FR),(FR,0, FR),(FR,FY, FR)]),     # right  x=+FR
        (-1, 0, [(-FR,FY,-FR),(-FR,0,-FR),(-FR,0,FR),(-FR,FY, FR)]), # left   x=-FR
    ]
    # Sort sides far-to-near by their center depth
    side_depths = []
    for nx,nz,pts in frame_sides:
        if ex*nx + ez*nz > 0:   # only draw faces visible to camera
            cx_ = sum(p[0] for p in pts)/4
            cz_ = sum(p[2] for p in pts)/4
            _, d = project_depth(cx_, FY/2, cz_)
            side_depths.append((d, pts))
    side_depths.sort(key=lambda x: -x[0])
    for _, pts in side_depths:
        draw_poly(surf, WOOD_S, pts)

    # Frame bottom
    draw_poly(surf, WOOD_BOT, [(-FR,FY,-FR),(FR,FY,-FR),(FR,FY,FR),(-FR,FY,FR)])

    # ── Phase 2: Squares + Pieces (sorted back-to-front) ──────────────────
    calls = []  # (depth, draw_fn)

    for r in range(8):
        for c in range(8):
            base_c = SQ_LIGHT if (r+c)%2==0 else SQ_DARK
            hl = highlights.get((r,c))
            if hl: base_c = hl

            corners3 = sq_corners(r, c, 0.0)
            cx_ = sum(p[0] for p in corners3)/4
            cz_ = sum(p[2] for p in corners3)/4
            _, d = project_depth(cx_, 0, cz_)

            def _sq(cc=corners3, bc=base_c):
                pts2 = [project(x,y,z) for x,y,z in cc]
                if all(p is not None for p in pts2):
                    ipx = [(int(p[0]),int(p[1])) for p in pts2]
                    pygame.draw.polygon(surf, bc, ipx)
                    pygame.draw.polygon(surf, (30,25,20), ipx, 1)

            calls.append((d, _sq))

    for r in range(8):
        for c in range(8):
            p = board.grid[r][c]
            if p:
                wcx, _, wcz = sq_center(r, c)
                _, d = project_depth(wcx, 0.5, wcz)
                calls.append((d, (lambda rr=r,cc=c,pp=p:
                    draw_piece(surf, pp.kind, pp.color, rr, cc))))

    calls.sort(key=lambda x: -x[0])
    for _, fn in calls:
        fn()

    # ── Coordinate labels ──────────────────────────────────────────────────
    files = 'abcdefgh' if not _flipped else 'hgfedcba'
    ranks = '12345678' if not _flipped else '87654321'
    font_sm = pygame.font.SysFont('consolas', 13, bold=True)
    for i in range(8):
        fp = project(i - 3.5, 0, FR + 0.1)
        if fp: surf.blit(font_sm.render(files[i], True, ACCENT), (int(fp[0])-5, int(fp[1])-8))
        rp = project(-FR - 0.1, 0, 3.5 - i)
        if rp: surf.blit(font_sm.render(ranks[i], True, ACCENT), (int(rp[0])-10, int(rp[1])-6))

# ─── Click detection ──────────────────────────────────────────────────────────
def pick_square(mx, my):
    """Return (r,c) of board square under mouse, or None."""
    best = None
    best_depth = float('inf')
    for r in range(8):
        for c in range(8):
            corners3 = sq_corners(r, c, 0.0)
            pts2 = [project(x,y,z) for x,y,z in corners3]
            if all(p is not None for p in pts2):
                if point_in_quad(mx, my, pts2):
                    cx_,_,cz_ = sq_center(r,c)
                    _, d = project_depth(cx_, 0, cz_)
                    if d < best_depth:
                        best_depth = d
                        best = (r, c)
    # Also check piece hitboxes (slightly above board)
    if best is None:
        for r in range(8):
            for c in range(8):
                corners3 = sq_corners(r, c, 1.0)
                pts2 = [project(x,y,z) for x,y,z in corners3]
                if all(p is not None for p in pts2):
                    if point_in_quad(mx, my, pts2):
                        cx_,_,cz_ = sq_center(r,c)
                        _, d = project_depth(cx_, 0.5, cz_)
                        if d < best_depth:
                            best_depth = d
                            best = (r, c)
    return best

# ─── Game state ───────────────────────────────────────────────────────────────
board     = Board()
selected  = None
leg_sq    = []
ai_side   = BLACK
ai_depth  = 3
_ai_busy  = False
_ai_mv    = None
_move_log = []
_anim     = None   # (piece_kind, piece_color, from_r, from_c, to_r, to_c, t, total)

def build_highlights():
    h = {}
    if board.move_history:
        lm = board.move_history[-1]
        h[lm.from_sq] = HL_LAST
        h[lm.to_sq]   = HL_LAST
    if board.is_check():
        kr,kc = board._king_pos(board.turn)
        if kr is not None: h[(kr,kc)] = HL_CHK
    if selected: h[selected] = HL_SEL
    for (tr,tc) in leg_sq:
        h[(tr,tc)] = HL_MOV
    return h

def ai_thread():
    global _ai_busy, _ai_mv
    _ai_mv   = best_move(board.clone(), depth=ai_depth)
    _ai_busy = False

def trigger_ai():
    global _ai_busy
    if board.turn==ai_side and not board.game_over() and not _ai_busy:
        _ai_busy = True
        threading.Thread(target=ai_thread, daemon=True).start()

def do_move(mv):
    global selected, leg_sq, _move_log
    piece = board.grid[mv.from_sq[0]][mv.from_sq[1]]
    r2,c2 = mv.to_sq
    if piece.kind==PAWN and mv.promotion is None and (r2==7 or r2==0):
        mv.promotion = QUEEN
    files='abcdefgh'
    r1,c1=mv.from_sq
    _move_log.append(f"{'W' if piece.color==WHITE else 'B'}: {files[c1]}{r1+1}→{files[c2]}{r2+1}")
    board.apply_move(mv)
    selected=None; leg_sq=[]
    trigger_ai()

def new_game():
    global board,selected,leg_sq,_ai_busy,_ai_mv,_move_log
    board=Board(); selected=None; leg_sq=[]; _ai_busy=False; _ai_mv=None; _move_log=[]
    trigger_ai()

def undo_move():
    global board,selected,leg_sq
    if len(board.move_history)<2: return
    hist=list(board.move_history[:-2])
    board=Board(); selected=None; leg_sq=[]
    for mv in hist: board.apply_move(mv)

def handle_click(r, c):
    global selected, leg_sq
    if board.game_over(): return
    if board.turn==ai_side: return
    piece=board.grid[r][c]
    if selected:
        for mv in board.legal_moves_from(*selected):
            if mv.to_sq==(r,c):
                do_move(mv); return
        selected=None; leg_sq=[]
    if piece and piece.color==board.turn:
        selected=(r,c)
        leg_sq=[(m.to_sq[0],m.to_sq[1]) for m in board.legal_moves_from(r,c)]

# ─── Sidebar UI ───────────────────────────────────────────────────────────────
def draw_sidebar(surf, fonts):
    fnt, fnt_sm, fnt_lg = fonts
    sx = W - 240
    pygame.draw.rect(surf, SIDEBAR, (sx, 0, 240, H))

    # Title
    t = fnt_lg.render('3D Chess', True, ACCENT)
    surf.blit(t, (sx+20, 18))

    # Turn indicator
    tc = (245, 240, 220) if board.turn==WHITE else (35, 28, 22)
    ring = (80,80,80) if board.turn==WHITE else (200,200,200)
    pygame.draw.circle(surf, ring, (sx+28, 68), 14)
    pygame.draw.circle(surf, tc,   (sx+28, 68), 11)
    who = 'White' if board.turn==WHITE else 'Black'
    surf.blit(fnt.render(f"{who}'s turn", True, TEXT_CLR), (sx+48, 60))

    # Status
    result = board.game_over()
    if result:
        lbl = fnt.render(result, True, ACCENT)
    elif board.is_check():
        lbl = fnt.render(f'{who} in CHECK!', True, (255,80,80))
    elif _ai_busy:
        dots = '.' * ((pygame.time.get_ticks()//350)%4)
        lbl = fnt.render(f'AI thinking{dots}', True, (120,180,255))
    else:
        lbl = fnt.render('', True, TEXT_CLR)
    surf.blit(lbl, (sx+14, 90))

    # Difficulty
    dn = {2:'Easy',3:'Medium',4:'Hard'}.get(ai_depth,'?')
    surf.blit(fnt_sm.render(f'Difficulty: {dn}', True, (150,150,180)), (sx+14, 115))
    surf.blit(fnt_sm.render(f'AI plays: {"Black" if ai_side==BLACK else "White"}',
                             True, (150,150,180)), (sx+14, 132))

    # Move log
    surf.blit(fnt_sm.render('Move Log', True, (130,130,165)), (sx+14, 160))
    for i, entry in enumerate(_move_log[-14:]):
        c_ = (200,200,210) if i%2==0 else (155,155,175)
        surf.blit(fnt_sm.render(entry, True, c_), (sx+14, 176+i*14))

    # Controls
    y = H-160
    for line in ['[A/D] Rotate  [W/S] Tilt',
                 '[Scroll] Zoom',
                 '[R] New  [U] Undo  [F] Flip',
                 '[1/2/3] Difficulty  [Q] Quit']:
        surf.blit(fnt_sm.render(line, True, (100,100,135)), (sx+10, y))
        y += 16

# ─── Main loop ────────────────────────────────────────────────────────────────
def main():
    global _azim, _elev, _dist, _flipped, ai_depth, ai_side, _ai_mv, selected, leg_sq

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption('3D Chess')
    clock  = pygame.time.Clock()

    fnt    = pygame.font.SysFont('segoeui', 17, bold=True)
    fnt_sm = pygame.font.SysFont('segoeui', 13)
    fnt_lg = pygame.font.SysFont('segoeui', 24, bold=True)
    fonts  = (fnt, fnt_sm, fnt_lg)

    trigger_ai()

    held = set()

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                held.add(event.key)
                if event.key == pygame.K_r: new_game()
                elif event.key == pygame.K_u: undo_move()
                elif event.key == pygame.K_f:
                    _flipped = not _flipped
                elif event.key == pygame.K_1: ai_depth = 2
                elif event.key == pygame.K_2: ai_depth = 3
                elif event.key == pygame.K_3: ai_depth = 4
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()

            if event.type == pygame.KEYUP:
                held.discard(event.key)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    if mx < W - 240:
                        sq = pick_square(mx, my)
                        if sq: handle_click(*sq)
                elif event.button == 4:  # scroll up = zoom in
                    _dist = max(8, _dist - 1.5)
                elif event.button == 5:  # scroll down = zoom out
                    _dist = min(40, _dist + 1.5)

        # Camera keys (held)
        spd = 1.2 * dt
        if pygame.K_a in held or pygame.K_LEFT  in held: _azim -= spd
        if pygame.K_d in held or pygame.K_RIGHT in held: _azim += spd
        if pygame.K_w in held or pygame.K_UP    in held: _elev = min(math.radians(80), _elev+spd*0.7)
        if pygame.K_s in held or pygame.K_DOWN  in held: _elev = max(math.radians(10), _elev-spd*0.7)
        if pygame.K_EQUALS in held or pygame.K_KP_PLUS  in held: _dist = max(8, _dist-8*dt)
        if pygame.K_MINUS  in held or pygame.K_KP_MINUS in held: _dist = min(40, _dist+8*dt)

        # AI result
        if _ai_mv is not None:
            mv = _ai_mv; _ai_mv = None
            if not board.game_over(): do_move(mv)

        # ── Render ──────────────────────────────────────────────────────────
        screen.fill(BG)
        hl = build_highlights()
        render_scene(screen, board, selected, leg_sq, hl)
        draw_sidebar(screen, fonts)

        # Game-over overlay
        result = board.game_over()
        if result:
            ov = pygame.Surface((500, 80), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 160))
            screen.blit(ov, (W//2-250, H//2-40))
            msg = fnt_lg.render(result, True, ACCENT)
            screen.blit(msg, (W//2 - msg.get_width()//2, H//2 - msg.get_height()//2))

        pygame.display.flip()

if __name__ == '__main__':
    main()
