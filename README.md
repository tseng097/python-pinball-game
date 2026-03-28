# Python Pinball Game

A simple pinball game built with **Python + Pygame + Pymunk**.

## Features
- Ball launcher (hold/release space)
- Left/right flippers (A/Left and D/Right)
- Bumpers and wall collisions
- Score + balls remaining
- Game over and restart

## Controls
- `Space` (hold/release): launcher power
- `A` or `←`: left flipper
- `D` or `→`: right flipper
- `R`: restart after game over
- `Esc`: quit

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Project structure
```
python-pinball-game/
├── main.py
├── requirements.txt
├── .gitignore
├── README.md
├── assets/
└── src/
    ├── game.py
    ├── entities.py
    └── settings.py
```

## Steam prep (next steps)
- Package with PyInstaller
- Add sounds/art polish
- Add settings menu + controller support
- Integrate Steamworks (achievements/cloud saves)
