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
├── chess_perspective.py  # 3D perspective UI (pygame, no ursina)
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

## License

MIT License — free to use, modify, and distribute.
