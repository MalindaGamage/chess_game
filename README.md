# ♟ Python Chess Game

A fully-featured chess game built in Python with **two UI modes**:

- **2D Animated** (`main.py`) — pygame with smooth piece animations and particle effects
- **3D Perspective** (`chess_perspective.py`) — pure pygame with real perspective projection, no external 3D engine required

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![pygame](https://img.shields.io/badge/pygame-2.6%2B-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Screenshots

### 3D Perspective View
Real perspective projection — rotate, tilt, and zoom the camera freely.

### 2D Animated View
Classic top-down board with smooth piece-glide animations and capture particle bursts.

---

## Features

| Feature | Details |
|---|---|
| Full chess rules | Castling, en passant, pawn promotion, 50-move draw, stalemate |
| AI opponent | Minimax with alpha-beta pruning + piece-square positional tables |
| 3 difficulty levels | Easy (depth 2) · Medium (depth 3) · Hard (depth 4) |
| 3D perspective view | Real camera math — orbit, tilt, zoom |
| 2D animated view | Smooth piece glide, capture particles, legal-move highlights |
| Check / checkmate detection | King glows red when in check |
| Move log | Last moves shown in sidebar |
| Captured pieces panel | Shown in sidebar (2D mode) |
| Flip board | Play from either side |
| Undo | Take back the last two half-moves |

---

## Project Structure

```
chess_game/
├── chess_engine.py       # Pure chess logic (board, move gen, rules)
├── ai_player.py          # Minimax AI with alpha-beta pruning
├── chess_perspective.py  # 3D perspective UI (pygame, no 3D engine)
├── main.py               # 2D animated UI (pygame)
└── assets.py             # Piece renderer for 2D mode
```

---

## Requirements

```
Python 3.10+
pygame >= 2.0
```

Install dependencies:

```bash
pip install pygame
```

---

## Running the Game

### 3D Perspective Mode (recommended)
```bash
python chess_perspective.py
```

### 2D Animated Mode
```bash
python main.py
```

---

## Controls

### 3D Mode

| Control | Action |
|---|---|
| **Left-click** a piece | Select it (legal moves highlighted in green) |
| **Left-click** a green square | Move the selected piece there |
| **A / D** or **← / →** | Rotate camera left / right |
| **W / S** or **↑ / ↓** | Tilt camera up / down |
| **Scroll wheel** | Zoom in / out |
| **R** | New game |
| **U** | Undo last move |
| **F** | Flip board |
| **1 / 2 / 3** | Set AI difficulty (Easy / Medium / Hard) |
| **Q** or **Escape** | Quit |

### 2D Mode

| Control | Action |
|---|---|
| **Left-click** | Select / move piece |
| **R** | New game |
| **U** | Undo |
| **F** | Flip board |
| **1 / 2 / 3** | Difficulty |
| **Q** | Quit |

---

## How It Works

### Chess Engine (`chess_engine.py`)
- Full legal-move generation for all piece types
- Castling rights tracking, en passant target square
- Check, checkmate, and stalemate detection
- 50-move rule draw

### AI (`ai_player.py`)
- **Minimax** algorithm with **alpha-beta pruning**
- **Move ordering** (captures first) for faster pruning
- **Piece-square tables** for positional awareness (pawns prefer centre, knights avoid edges, etc.)
- Material evaluation: Pawn=100, Knight=320, Bishop=330, Rook=500, Queen=900

### 3D Renderer (`chess_perspective.py`)
- Spherical camera (azimuth + elevation) with `lookAt` view matrix
- Perspective projection: world → camera space → screen
- **Painter's algorithm** — objects sorted far-to-near and drawn back-to-front
- Pieces rendered as compound 3D shapes (cylinders via disc-ring projection, spheres)

---

## Concepts & Technologies

### Programming Languages & Tools

| Tool | Usage |
|---|---|
| **Python 3.10+** | Core language |
| **pygame 2.6** | 2D rendering, input handling, animation |
| **Git** | Version control |
| **GitHub** | Code hosting and collaboration |
| **VS Code** | Development IDE |

---

### Python Core Concepts

| Concept | Where Used |
|---|---|
| **Dataclasses** (`@dataclass`) | `Piece`, `Move` in chess_engine.py |
| **Type hints** (`Optional`, `list[Move]`) | Function signatures throughout |
| **OOP — Classes & Objects** | `Board`, `Piece`, `Move`, `AnimPiece`, `Particle` |
| **Threading** | AI runs on a background thread so the UI stays responsive |
| **Closures & Lambda** | Painter's algorithm deferred draw call list |
| **List comprehensions** | Move generation, filtering legal moves |
| **Dictionary** | Square entities, piece roots, highlight map |
| **f-strings** | Move log notation, status messages |
| **Default parameters** | `def sq_corners(r, c, y=0.0)` |
| **`__name__ == '__main__'`** | Entry point guard in all game files |
| **`sys.path.insert`** | Cross-file module imports on Windows |
| **Clone / Deep copy pattern** | `board.clone()` creates isolated copies for AI tree search |
| **Tuple unpacking** | `r1, c1 = move.from_sq` |
| **Optional type** | `Optional[Piece]`, `Optional[int]` for nullable values |

---

### Software Architecture & Design Patterns

| Pattern | How It Is Applied |
|---|---|
| **MVC — Model / View separation** | `chess_engine.py` = Model · `chess_perspective.py` / `main.py` = View |
| **Factory Pattern** | `make_piece(kind, side, r, c)` builds compound 3D piece objects |
| **Painter's Algorithm** | Draw calls collected → sorted by depth → executed back-to-front |
| **Strategy Pattern** | AI depth (difficulty) is a swappable parameter |
| **Clone Pattern** | `board.clone()` isolates each minimax branch |
| **Observer-like pattern** | `update_status()` reads game state and reflects it in the UI |
| **Separation of Concerns** | Engine has no rendering code; AI has no UI code |
| **Lazy evaluation** | Legal moves generated only when a piece is selected |
| **Deferred execution** | Lambda draw calls collected in a list and executed after depth-sorting |

---

### Data Structures & Algorithms

| Concept | Usage |
|---|---|
| **2D Array (8×8 grid)** | Board representation `grid[row][col]` |
| **List of tuples** | Move history, legal move target squares |
| **Dictionary** | Square entities, piece roots, highlight colour map |
| **Stack (implicit)** | Minimax recursion call stack |
| **Sorting** | Painter's algorithm — `calls.sort(key=lambda x: -x[0])` |
| **Filtering** | `[m for m in moves if not self._leaves_king_in_check(m)]` |
| **Set** | Held keyboard keys for smooth camera rotation |
| **Ray casting algorithm** | `point_in_quad()` — detects if a mouse click is inside a projected square |
| **Depth-first search** | Minimax explores the game tree depth-first |
| **Move ordering** | Captures sorted first for better alpha-beta pruning efficiency |
| **Alpha-Beta Pruning** | Cuts branches where `beta ≤ alpha` — no effect on result |

---

### Artificial Intelligence Concepts

| Concept | Details |
|---|---|
| **Minimax Algorithm** | Two-player zero-sum adversarial search — White maximises, Black minimises |
| **Alpha-Beta Pruning** | Skips branches that cannot affect the final decision — reduces nodes from O(b^d) to O(b^(d/2)) |
| **Game Tree** | Every possible move expands into a tree of future board states |
| **Search Depth** | Difficulty controls half-moves looked ahead: Easy=2, Medium=3, Hard=4 |
| **Static Evaluation Function** | Scores a position without further search (material + positional) |
| **Material Evaluation** | Pawn=100, Knight=320, Bishop=330, Rook=500, Queen=900, King=20000 (centipawns) |
| **Piece-Square Tables** | Positional bonuses per piece per square (pawns rewarded for advancing, knights penalised on rim) |
| **Move Ordering** | Captures evaluated first → earlier beta cutoffs → faster search |
| **Zero-Sum Game** | White's gain equals Black's loss — one evaluation function serves both |
| **Perfect Information Game** | Both players see the full board — no hidden state |
| **Multithreaded AI** | AI runs on `threading.Thread` so the window stays interactive |

---

### Mathematics Concepts

#### Linear Algebra

| Concept | Usage |
|---|---|
| **3D Vectors** | Camera position, piece positions, face normals |
| **Vector subtraction** | `t = point − camera_eye` translates point into camera space |
| **Dot product** | Computes depth (`dot(forward, t)`) and face visibility |
| **Cross product** | `forward × world_up` = right axis; `right × forward` = up axis |
| **Vector normalisation** | `v / |v|` produces unit-length basis vectors |
| **Orthonormal basis** | Right, Up, Forward — three perpendicular camera axes |
| **LookAt / View Matrix** | Transforms world coordinates into camera-relative space |
| **Basis change** | World space → Camera space using dot products with basis vectors |

#### Coordinate Systems & Projection

| Concept | Usage |
|---|---|
| **World space** | 3D chess board centred at the origin |
| **Camera space** | World rotated so the camera looks along +Z |
| **Screen space** | Final 2D pixel coordinates for drawing |
| **Perspective projection** | `sx = W/2 + FOV × cx / cz` — near objects appear larger |
| **Perspective divide** | Dividing by depth `cz` creates natural foreshortening |
| **Spherical coordinates** | Camera orbit: `x = dist · sin(azim) · cos(elev)` |
| **Coordinate centering** | Board squares mapped to −4 to +4 on both axes, centred at origin |

#### Trigonometry

| Concept | Usage |
|---|---|
| **sin / cos** | Camera position from azimuth and elevation angles |
| **atan2** | Camera angle relative to a piece for back-face culling |
| **Radians ↔ Degrees** | `math.radians()` converts user-friendly degree inputs |
| **Circular distribution** | Queen crown spires and cylinder rings: `x = r · cos(2πi/n)` |

#### Animation & Interpolation

| Concept | Usage |
|---|---|
| **Linear interpolation (lerp)** | `a + (b−a) × t` — smooth piece movement between squares |
| **Cubic ease-out** | `1 − (1−t)³` — pieces decelerate as they arrive at the target |
| **Parabolic arc** | Pieces rise to a midpoint then descend during the slide animation |
| **Delta time** | `dt = clock.tick(FPS) / 1000` — frame-rate independent camera speed |
| **Frame-based animation** | Particle positions updated every frame with velocity and gravity |

---

### Chess-Specific Concepts

| Concept | Implementation |
|---|---|
| **Piece types** | Pawn, Knight, Bishop, Rook, Queen, King |
| **Color sides** | WHITE = +1, BLACK = −1 (used directly in evaluation arithmetic) |
| **Legal move generation** | Per-piece rules then filtered — any move that leaves the king in check is illegal |
| **Sliding pieces** | Bishop / Rook / Queen slide along rays until blocked or capturing |
| **Castling** | Kingside and queenside — checks rights, empty squares, king not passing through check |
| **En passant** | Target square stored after a double pawn push; captured pawn removed on next ply |
| **Pawn promotion** | Detected when pawn reaches back rank — auto-promotes to Queen |
| **Check detection** | Is the king's square attacked by any opponent piece? |
| **Checkmate** | In check AND no legal moves exist |
| **Stalemate** | Not in check AND no legal moves exist |
| **50-move rule** | `halfmove_clock >= 100` → draw |
| **Half-move clock** | Resets on any capture or pawn move |
| **Full-move number** | Increments after Black's move |
| **Move history** | Full list of applied moves — used for undo and last-move highlight |
| **Piece-square tables** | Separate positional tables for Pawn, Knight, Bishop, Rook, Queen, King |
| **Algebraic notation** | `e2→e4` format displayed in the move log |

---

### Rendering & Graphics Concepts

| Concept | Usage |
|---|---|
| **Painter's Algorithm** | All objects sorted by depth and drawn far-to-near |
| **Depth sorting (Z-sorting)** | `calls.sort(key=lambda x: -x[0])` |
| **Back-face culling** | Frame sides skipped when `camera · normal < 0` (facing away) |
| **Polygon rasterisation** | `pygame.draw.polygon()` fills projected quads and disc rings |
| **Double buffering** | `pygame.display.flip()` prevents screen tearing |
| **Procedural geometry** | Cylinder discs generated as rings of `n` projected 3D points |
| **Compound objects** | Each 3D piece = multiple primitives (cylinders + spheres + cubes) |
| **Highlight overlays** | Colour overlays on selected, legal-move, last-move, and check squares |
| **Particle system** | Capture burst effect: velocity, gravity, size and opacity fade over lifetime |
| **Easing curves** | Smooth camera and piece movement using cubic ease-out |
| **Screen-space UI** | Sidebar text drawn as 2D overlay on top of the 3D scene |
| **Lambert shading (approx)** | Lighter top faces, darker side faces on pieces for depth illusion |
| **Specular highlight (approx)** | Small bright circle offset from sphere centre simulates light reflection |

---

### Game Development Concepts

| Concept | Usage |
|---|---|
| **Game loop** | `while True: handle_events → update → render` |
| **FPS control** | `clock.tick(60)` caps the frame rate to 60 FPS |
| **Event system** | `pygame.event.get()` processes keyboard, mouse, and quit events |
| **Held-key input** | `held = set()` tracks keys held down for smooth continuous camera rotation |
| **Implicit state machine** | Idle → piece selected → legal moves shown → move executed → AI turn |
| **3D hit detection** | Ray casting point-in-polygon for picking a board square from a 2D mouse click |
| **Game-over detection** | Checkmate / stalemate / 50-move rule checked after every move |
| **Undo system** | Replay all moves except the last two from a fresh board |
| **AI turn management** | `board.turn == ai_side` gate prevents the human from clicking during AI thinking |
| **Spherical orbit camera** | Camera controlled by azimuth, elevation, and distance parameters |
| **HUD / Sidebar** | Status text, move log, difficulty indicator, controls guide overlaid on screen |

---

### Software Engineering Practices

| Practice | Applied |
|---|---|
| **Modular design** | 5 files with clearly separated responsibilities |
| **Version control (Git)** | Commits, `.gitignore`, branch management |
| **Documentation** | README covering features, controls, architecture, and all concepts |
| **Open source licensing** | MIT License |
| **Defensive coding** | `if p is None: return`, `try/except` for optional attributes |
| **Incremental testing** | Validation scripts run before each launch to catch errors early |
| **Minimal dependencies** | Only `pygame` required — no heavy frameworks |
| **Cross-platform pathing** | `sys.path.insert` for reliable imports on Windows |

---

### Concept Summary Map

```
Python ──────────────── OOP · Threading · Dataclasses · Type hints · Lambdas
Algorithms ─────────── Minimax · Alpha-Beta · Ray casting · Depth sort · Move ordering
Mathematics ────────── Linear algebra · Perspective projection · Trig · Interpolation
Chess Logic ────────── Move gen · Check/Checkmate · Castling · En passant · Promotion
Rendering ──────────── Painter's algo · Projection · Particles · Easing · Shading
Game Dev ───────────── Game loop · Input · State machine · Camera · HUD · Hit detection
Software Eng ───────── MVC · Git · Docs · License · Modular design · Separation of concerns
```

> This project covers **Computer Science fundamentals**, **Game AI**, **3D Graphics Mathematics**,
> **Software Architecture**, and **full-stack game development** — all in pure Python.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.

Copyright (c) 2026 pkgmalinda@gmail.com
