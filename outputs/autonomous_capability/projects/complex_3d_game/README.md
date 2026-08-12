# 3D Pong Arena

Generated from:

```text
Build a fully playable complex 3D browser game with scoring, controls, physics, menus, and tests.
```

## Run

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- Game: http://localhost:13000
- API health: http://localhost:18000/health

## Gameplay

- Move your paddle with `W/S`, `ArrowUp/ArrowDown`, mouse, or touch.
- The AI paddle tracks the ball with limited reaction speed.
- First player to 7 wins.
- Press `Space` to pause/resume.
- Press `R` to restart.

This is a playable game project, not a SaaS dashboard.
