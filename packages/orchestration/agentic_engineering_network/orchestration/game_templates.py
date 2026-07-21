from __future__ import annotations

import re


def build_game_project_artifacts(idea: str, run_id: str) -> dict[str, str]:
    slug = _slugify(idea)
    base = f"{slug}-{run_id[:8]}"
    title = "3D Pong Arena"
    return {
        f"{base}/README.md": _readme(title, idea),
        f"{base}/.env.example": _env_example(),
        f"{base}/docker-compose.yml": _compose(),
        f"{base}/apps/api/Dockerfile": _api_dockerfile(),
        f"{base}/apps/api/requirements.txt": _api_requirements(),
        f"{base}/apps/api/alembic.ini": _alembic_ini(),
        f"{base}/apps/api/app/__init__.py": "",
        f"{base}/apps/api/app/main.py": _api_main(),
        f"{base}/apps/api/migrations/env.py": _alembic_env(),
        f"{base}/apps/api/migrations/script.py.mako": _alembic_script(),
        f"{base}/apps/api/migrations/versions/0001_initial.py": _alembic_initial_revision(),
        f"{base}/apps/api/tests/test_health.py": _api_test_health(),
        f"{base}/apps/web/Dockerfile": _web_dockerfile(),
        f"{base}/apps/web/Dockerfile.e2e": _web_e2e_dockerfile(),
        f"{base}/apps/web/package.json": _web_package(),
        f"{base}/apps/web/next.config.ts": _web_next_config(),
        f"{base}/apps/web/playwright.config.ts": _playwright_config(),
        f"{base}/apps/web/vitest.config.ts": _vitest_config(),
        f"{base}/apps/web/tsconfig.json": _web_tsconfig(),
        f"{base}/apps/web/src/app/layout.tsx": _web_layout(title),
        f"{base}/apps/web/src/app/page.tsx": _web_page(),
        f"{base}/apps/web/src/app/globals.css": _web_globals(),
        f"{base}/apps/web/src/game/controls.ts": _game_controls(),
        f"{base}/apps/web/src/game/physics.ts": _game_physics(),
        f"{base}/apps/web/src/game/physics.test.ts": _game_physics_test(),
        f"{base}/apps/web/src/game/scene.ts": _game_scene(),
        f"{base}/apps/web/tests/workbench.spec.ts": _web_e2e(),
        f"{base}/apps/desktop/package.json": _desktop_package(title),
        f"{base}/apps/desktop/src/main.js": _desktop_main(title),
        f"{base}/database/schema.sql": _schema_sql(),
        f"{base}/docs/SPEC.md": _spec(idea),
        f"{base}/docs/ARCHITECTURE.md": _architecture(),
        f"{base}/docs/SECURITY.md": _security_doc(),
        f"{base}/docs/PROJECT_KIND.md": "project_kind: game\nprimary_experience: playable_3d_pong\n",
        f"{base}/scripts/start.ps1": _start_script(),
        f"{base}/scripts/test.ps1": _test_script(),
        f"{base}/scripts/package-windows.ps1": _package_windows_script(),
    }


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "generated-game"


def _readme(title: str, idea: str) -> str:
    return f"""# {title}

Generated from:

```text
{idea}
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
"""


def _env_example() -> str:
    return """API_PORT=18000
WEB_PORT=13000
NEXT_PUBLIC_API_URL=http://localhost:18000
"""


def _compose() -> str:
    return """services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: game
      POSTGRES_PASSWORD: change-me
      POSTGRES_DB: game
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U game -d game"]
      interval: 5s
      timeout: 3s
      retries: 20

  api:
    build:
      context: ./apps/api
    ports:
      - "${API_PORT:-18000}:8000"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 10

  web:
    build:
      context: ./apps/web
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:18000}
      NEXT_TELEMETRY_DISABLED: "1"
    ports:
      - "${WEB_PORT:-13000}:3000"
    depends_on:
      api:
        condition: service_healthy

  e2e:
    profiles: ["test"]
    build:
      context: ./apps/web
      dockerfile: Dockerfile.e2e
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:18000}
      NEXT_TELEMETRY_DISABLED: "1"
    volumes:
      - ./apps/web/test-results:/app/test-results
      - ./apps/web/playwright-report:/app/playwright-report
"""


def _api_dockerfile() -> str:
    return """FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.1.2" \
    && python -m pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY tests ./tests
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def _api_requirements() -> str:
    return """fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pytest>=8.0.0
httpx>=0.27.0
pip-audit>=2.9.0
"""


def _api_main() -> str:
    return """from fastapi import FastAPI

app = FastAPI(title="3D Pong Arena API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "3d-pong-arena"}
"""


def _api_test_health() -> str:
    return """from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    assert TestClient(app).get("/health").json()["status"] == "ok"
"""


def _alembic_ini() -> str:
    return """[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///./game.db
"""


def _alembic_env() -> str:
    return """from alembic import context


def run_migrations_offline() -> None:
    context.configure(url="sqlite:///./game.db")
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    run_migrations_offline()


run_migrations_online()
"""


def _alembic_script() -> str:
    return """\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
\"\"\"
"""


def _alembic_initial_revision() -> str:
    return '''"""initial game schema

Revision ID: 0001_initial
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "game_scores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("player_score", sa.Integer, nullable=False),
        sa.Column("ai_score", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("game_scores")
'''


def _web_dockerfile() -> str:
    return """FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
"""


def _web_e2e_dockerfile() -> str:
    return """FROM mcr.microsoft.com/playwright:v1.57.0-noble
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV NEXT_TELEMETRY_DISABLED=1
CMD ["npm", "run", "e2e"]
"""


def _web_package() -> str:
    return """{
  "name": "generated-3d-pong-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev -H 0.0.0.0",
    "build": "next build",
    "start": "next start -H 0.0.0.0",
    "test": "vitest run",
    "e2e": "playwright test"
  },
  "dependencies": {
    "next": "^16.2.0",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "three": "^0.180.0"
  },
  "devDependencies": {
    "@playwright/test": "1.57.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@types/three": "^0.180.0",
    "typescript": "^5.9.0",
    "vitest": "^3.2.0"
  },
  "overrides": {
    "postcss": "8.5.20"
  }
}
"""


def _web_next_config() -> str:
    return """import type { NextConfig } from "next";

const nextConfig: NextConfig = { allowedDevOrigins: ["127.0.0.1"] };
export default nextConfig;
"""


def _vitest_config() -> str:
    return '''import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    exclude: ["tests/**", "node_modules/**", ".next/**"],
  },
});
'''


def _web_tsconfig() -> str:
    return """{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [{ "name": "next" }]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""


def _web_layout(title: str) -> str:
    return f"""import "./globals.css";

export const metadata = {{
  title: "{title}",
  description: "Playable 3D Pong game with score and AI opponent"
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en">
      <body>{{children}}</body>
    </html>
  );
}}
"""


def _legacy_web_page() -> str:
    return r'''"use client";

import { useEffect, useRef, useState } from "react";

type GameState = {
  player: number;
  ai: number;
  ballX: number;
  ballY: number;
  ballZ: number;
  velocityX: number;
  velocityY: number;
  velocityZ: number;
  playerScore: number;
  aiScore: number;
  paused: boolean;
  winner: string;
};

const initialState = (): GameState => ({
  player: 0,
  ai: 0,
  ballX: 0,
  ballY: 0,
  ballZ: 0,
  velocityX: 0.55,
  velocityY: 0.38,
  velocityZ: 0.72,
  playerScore: 0,
  aiScore: 0,
  paused: false,
  winner: ""
});

export default function Home() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const stateRef = useRef<GameState>(initialState());
  const keysRef = useRef<Set<string>>(new Set());
  const [score, setScore] = useState({ player: 0, ai: 0, winner: "", paused: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    const activeCanvas = canvas;
    const activeContext = context;

    function resize() {
      activeCanvas.width = Math.floor(activeCanvas.clientWidth * window.devicePixelRatio);
      activeCanvas.height = Math.floor(activeCanvas.clientHeight * window.devicePixelRatio);
    }

    function resetBall(direction: number) {
      const state = stateRef.current;
      state.ballX = 0;
      state.ballY = 0;
      state.ballZ = 0;
      state.velocityX = 0.48 * direction;
      state.velocityY = (Math.random() > 0.5 ? 0.35 : -0.35);
      state.velocityZ = (Math.random() > 0.5 ? 0.68 : -0.68);
    }

    function project(x: number, y: number, z: number) {
      const depth = 900;
      const scale = depth / (depth + z * 220);
      return {
        x: activeCanvas.width / 2 + x * activeCanvas.width * 0.33 * scale,
        y: activeCanvas.height / 2 + y * activeCanvas.height * 0.34 * scale,
        scale
      };
    }

    function drawCourt() {
      const corners = [
        project(-1, -1, -1),
        project(1, -1, -1),
        project(1, 1, -1),
        project(-1, 1, -1),
        project(-1, -1, 1),
        project(1, -1, 1),
        project(1, 1, 1),
        project(-1, 1, 1)
      ];
      activeContext.strokeStyle = "rgba(98, 242, 255, 0.32)";
      activeContext.lineWidth = 2 * window.devicePixelRatio;
      const edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
      for (const [a, b] of edges) {
        activeContext.beginPath();
        activeContext.moveTo(corners[a].x, corners[a].y);
        activeContext.lineTo(corners[b].x, corners[b].y);
        activeContext.stroke();
      }
      activeContext.setLineDash([12 * window.devicePixelRatio, 16 * window.devicePixelRatio]);
      activeContext.beginPath();
      const top = project(0, -1, 0);
      const bottom = project(0, 1, 0);
      activeContext.moveTo(top.x, top.y);
      activeContext.lineTo(bottom.x, bottom.y);
      activeContext.stroke();
      activeContext.setLineDash([]);
    }

    function drawPaddle(z: number, y: number, color: string) {
      const center = project(z < 0 ? -0.95 : 0.95, y, z);
      const width = 30 * center.scale * window.devicePixelRatio;
      const height = 130 * center.scale * window.devicePixelRatio;
      activeContext.fillStyle = color;
      activeContext.shadowColor = color;
      activeContext.shadowBlur = 24 * center.scale;
      activeContext.fillRect(center.x - width / 2, center.y - height / 2, width, height);
      activeContext.shadowBlur = 0;
    }

    function drawBall() {
      const state = stateRef.current;
      const ball = project(state.ballX, state.ballY, state.ballZ);
      const radius = 16 * ball.scale * window.devicePixelRatio;
      const gradient = activeContext.createRadialGradient(ball.x - radius / 3, ball.y - radius / 3, radius / 6, ball.x, ball.y, radius);
      gradient.addColorStop(0, "#ffffff");
      gradient.addColorStop(1, "#f8d14a");
      activeContext.fillStyle = gradient;
      activeContext.shadowColor = "#f8d14a";
      activeContext.shadowBlur = 28;
      activeContext.beginPath();
      activeContext.arc(ball.x, ball.y, radius, 0, Math.PI * 2);
      activeContext.fill();
      activeContext.shadowBlur = 0;
    }

    function step() {
      const state = stateRef.current;
      if (!state.paused && !state.winner) {
        const keys = keysRef.current;
        if (keys.has("w") || keys.has("arrowup")) state.player -= 0.045;
        if (keys.has("s") || keys.has("arrowdown")) state.player += 0.045;
        state.player = Math.max(-0.75, Math.min(0.75, state.player));
        state.ai += (state.ballY - state.ai) * 0.045;
        state.ai = Math.max(-0.75, Math.min(0.75, state.ai));
        state.ballX += state.velocityX * 0.018;
        state.ballY += state.velocityY * 0.018;
        state.ballZ += state.velocityZ * 0.018;
        if (Math.abs(state.ballY) > 0.95) state.velocityY *= -1;
        if (Math.abs(state.ballX) > 0.95) state.velocityX *= -1;
        if (state.ballZ < -1) {
          if (Math.abs(state.ballY - state.player) < 0.28) {
            state.ballZ = -1;
            state.velocityZ = Math.abs(state.velocityZ) + 0.035;
            state.velocityY += (state.ballY - state.player) * 0.7;
          } else {
            state.aiScore += 1;
            resetBall(1);
          }
        }
        if (state.ballZ > 1) {
          if (Math.abs(state.ballY - state.ai) < 0.28) {
            state.ballZ = 1;
            state.velocityZ = -Math.abs(state.velocityZ) - 0.035;
            state.velocityY += (state.ballY - state.ai) * 0.55;
          } else {
            state.playerScore += 1;
            resetBall(-1);
          }
        }
        if (state.playerScore >= 7) state.winner = "YOU WIN";
        if (state.aiScore >= 7) state.winner = "AI WINS";
      }
      activeContext.clearRect(0, 0, activeCanvas.width, activeCanvas.height);
      const bg = activeContext.createLinearGradient(0, 0, activeCanvas.width, activeCanvas.height);
      bg.addColorStop(0, "#050713");
      bg.addColorStop(1, "#10192f");
      activeContext.fillStyle = bg;
      activeContext.fillRect(0, 0, activeCanvas.width, activeCanvas.height);
      drawCourt();
      drawPaddle(-1, state.player, "#62f2ff");
      drawPaddle(1, state.ai, "#ff4d8d");
      drawBall();
      setScore({ player: state.playerScore, ai: state.aiScore, winner: state.winner, paused: state.paused });
      requestAnimationFrame(step);
    }

    function keyDown(event: KeyboardEvent) {
      const key = event.key.toLowerCase();
      if (key === " ") stateRef.current.paused = !stateRef.current.paused;
      if (key === "r") stateRef.current = initialState();
      keysRef.current.add(key);
    }
    function keyUp(event: KeyboardEvent) {
      keysRef.current.delete(event.key.toLowerCase());
    }
    function pointer(event: PointerEvent) {
      const rect = activeCanvas.getBoundingClientRect();
      const y = ((event.clientY - rect.top) / rect.height) * 2 - 1;
      stateRef.current.player = Math.max(-0.75, Math.min(0.75, y));
    }

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("keydown", keyDown);
    window.addEventListener("keyup", keyUp);
    activeCanvas.addEventListener("pointermove", pointer);
    const frame = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
      window.removeEventListener("keydown", keyDown);
      window.removeEventListener("keyup", keyUp);
      activeCanvas.removeEventListener("pointermove", pointer);
    };
  }, []);

  return (
    <main className="game-shell">
      <section className="hud">
        <div>
          <p>3D PONG ARENA</p>
          <h1>{score.player} : {score.ai}</h1>
        </div>
        <div className="status">{score.winner || (score.paused ? "PAUSED" : "FIRST TO 7")}</div>
      </section>
      <canvas ref={canvasRef} className="game-canvas" aria-label="Playable 3D Pong arena" />
      <section className="controls">
        <span>W/S or Arrow keys</span>
        <span>Mouse/touch moves paddle</span>
        <span>Space pause</span>
        <span>R restart</span>
      </section>
    </main>
  );
}
'''


def _web_page() -> str:
    return '''"use client";

import { useEffect, useRef, useState } from "react";

import { createControls } from "../game/controls";
import { createInitialState, stepGame, type GameState } from "../game/physics";
import { createGameScene } from "../game/scene";

const EMPTY_HUD = createInitialState();

export default function Home() {
  const arenaRef = useRef<HTMLDivElement | null>(null);
  const stateRef = useRef<GameState>(EMPTY_HUD);
  const [snapshot, setSnapshot] = useState(EMPTY_HUD);

  useEffect(() => {
    const container = arenaRef.current;
    if (!container) return;
    const scene = createGameScene(container);
    const controls = createControls(container);
    let previous = performance.now();
    let lastHudUpdate = 0;
    let frame = 0;

    function animate(now: number) {
      const delta = Math.min((now - previous) / 1000, 0.05);
      previous = now;
      stateRef.current = stepGame(stateRef.current, controls.axis(), delta);
      scene.render(stateRef.current);
      if (now - lastHudUpdate > 50) {
        setSnapshot(stateRef.current);
        lastHudUpdate = now;
      }
      frame = requestAnimationFrame(animate);
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === " ") {
        event.preventDefault();
        stateRef.current = { ...stateRef.current, paused: !stateRef.current.paused };
      }
      if (event.key.toLowerCase() === "r") stateRef.current = createInitialState();
    }

    window.addEventListener("keydown", onKeyDown);
    frame = requestAnimationFrame(animate);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("keydown", onKeyDown);
      controls.dispose();
      scene.dispose();
    };
  }, []);

  const winnerText = snapshot.winner === "player"
    ? "PLAYER WINS"
    : snapshot.winner === "ai"
      ? "AI WINS"
      : snapshot.paused
        ? "PAUSED"
        : "FIRST TO 7";

  function togglePause() {
    stateRef.current = { ...stateRef.current, paused: !stateRef.current.paused };
  }

  function restart() {
    stateRef.current = createInitialState();
    setSnapshot(stateRef.current);
  }

  return (
    <main className="game-shell">
      <section className="hud">
        <div><p>NEON CIRCUIT</p><h1>3D PONG ARENA</h1></div>
        <div className="score"><strong>{snapshot.playerScore}</strong><span>{winnerText}</span><strong>{snapshot.aiScore}</strong></div>
        <div className="actions">
          <button type="button" onClick={togglePause}>{snapshot.paused ? "Resume" : "Pause"}</button>
          <button type="button" onClick={restart}>Restart</button>
        </div>
      </section>
      <div
        aria-label="Playable Three.js WebGL canvas for 3D Pong"
        className="arena"
        data-renderer="three-webgl-canvas"
        ref={arenaRef}
      />
      <section className="controls">
        <span>W/S or Arrow keys</span><span>Mouse/touch moves paddle</span><span>Space pause</span><span>R restart</span>
      </section>
    </main>
  );
}
'''


def _playwright_config() -> str:
    return '''import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  outputDir: "./test-results",
  reporter: [["line"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: { baseURL: "http://127.0.0.1:3000", headless: true, screenshot: "on", trace: "retain-on-failure" },
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
    timeout: 120_000
  }
});
'''


def _game_controls() -> str:
    return '''export type Controls = {
  axis: () => number;
  dispose: () => void;
};

export function createControls(target: HTMLElement): Controls {
  const keys = new Set<string>();
  let pointerAxis = 0;
  let pointerActive = false;

  const keyDown = (event: KeyboardEvent) => keys.add(event.key.toLowerCase());
  const keyUp = (event: KeyboardEvent) => keys.delete(event.key.toLowerCase());
  const pointerMove = (event: PointerEvent) => {
    const bounds = target.getBoundingClientRect();
    pointerAxis = Math.max(-1, Math.min(1, ((event.clientY - bounds.top) / bounds.height) * 2 - 1));
    pointerActive = true;
  };
  const pointerLeave = () => { pointerActive = false; };

  window.addEventListener("keydown", keyDown);
  window.addEventListener("keyup", keyUp);
  target.addEventListener("pointermove", pointerMove);
  target.addEventListener("pointerleave", pointerLeave);

  return {
    axis: () => {
      if (pointerActive) return pointerAxis;
      const up = keys.has("w") || keys.has("arrowup") ? -1 : 0;
      const down = keys.has("s") || keys.has("arrowdown") ? 1 : 0;
      return up + down;
    },
    dispose: () => {
      window.removeEventListener("keydown", keyDown);
      window.removeEventListener("keyup", keyUp);
      target.removeEventListener("pointermove", pointerMove);
      target.removeEventListener("pointerleave", pointerLeave);
    }
  };
}
'''


def _game_physics() -> str:
    return '''export type Winner = "player" | "ai" | null;

export type GameState = {
  playerY: number;
  aiY: number;
  ball: { x: number; y: number; z: number };
  velocity: { x: number; y: number; z: number };
  playerScore: number;
  aiScore: number;
  paused: boolean;
  winner: Winner;
  rally: number;
};

const LIMIT_Y = 3.2;
const LIMIT_X = 4.6;
const PADDLE_Z = 5.2;
const GOAL_Z = 6.1;
const PADDLE_HALF_HEIGHT = 1.35;

export function createInitialState(direction = -1): GameState {
  return {
    playerY: 0,
    aiY: 0,
    ball: { x: 0, y: 0, z: 0 },
    velocity: { x: 2.2, y: 1.7, z: 5.5 * direction },
    playerScore: 0,
    aiScore: 0,
    paused: false,
    winner: null,
    rally: 0
  };
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function serve(state: GameState, direction: number): GameState {
  return {
    ...state,
    ball: { x: 0, y: 0, z: 0 },
    velocity: { x: direction * 1.7, y: direction * -1.25, z: direction * 5.5 },
    rally: 0
  };
}

export function stepGame(current: GameState, inputAxis: number, deltaSeconds: number): GameState {
  if (current.paused || current.winner || deltaSeconds <= 0) return current;
  const delta = Math.min(deltaSeconds, 0.05);
  let state: GameState = {
    ...current,
    playerY: clamp(current.playerY + clamp(inputAxis, -1, 1) * 7.5 * delta, -LIMIT_Y, LIMIT_Y),
    aiY: clamp(current.aiY + clamp(current.ball.y - current.aiY, -1, 1) * 4.7 * delta, -LIMIT_Y, LIMIT_Y),
    ball: {
      x: current.ball.x + current.velocity.x * delta,
      y: current.ball.y + current.velocity.y * delta,
      z: current.ball.z + current.velocity.z * delta
    },
    velocity: { ...current.velocity }
  };

  if (Math.abs(state.ball.x) >= LIMIT_X) {
    state.ball.x = clamp(state.ball.x, -LIMIT_X, LIMIT_X);
    state.velocity.x *= -1;
  }
  if (Math.abs(state.ball.y) >= LIMIT_Y) {
    state.ball.y = clamp(state.ball.y, -LIMIT_Y, LIMIT_Y);
    state.velocity.y *= -1;
  }
  const atPlayer = state.ball.z <= -PADDLE_Z && state.velocity.z < 0;
  const atAi = state.ball.z >= PADDLE_Z && state.velocity.z > 0;
  if (atPlayer && Math.abs(state.ball.y - state.playerY) <= PADDLE_HALF_HEIGHT) {
    state.ball.z = -PADDLE_Z;
    state.velocity.z = Math.abs(state.velocity.z) * 1.035;
    state.velocity.y += (state.ball.y - state.playerY) * 1.15;
    state.rally += 1;
  }
  if (atAi && Math.abs(state.ball.y - state.aiY) <= PADDLE_HALF_HEIGHT) {
    state.ball.z = PADDLE_Z;
    state.velocity.z = -Math.abs(state.velocity.z) * 1.03;
    state.velocity.y += (state.ball.y - state.aiY) * 0.9;
    state.rally += 1;
  }
  if (state.ball.z < -GOAL_Z) {
    state = serve({ ...state, aiScore: state.aiScore + 1 }, 1);
  } else if (state.ball.z > GOAL_Z) {
    state = serve({ ...state, playerScore: state.playerScore + 1 }, -1);
  }
  if (state.playerScore >= 7) state.winner = "player";
  if (state.aiScore >= 7) state.winner = "ai";
  return state;
}
'''


def _game_physics_test() -> str:
    return '''import { describe, expect, it } from "vitest";

import { createInitialState, stepGame } from "./physics";

describe("3D Pong physics", () => {
  it("moves the player within arena bounds", () => {
    let state = createInitialState();
    for (let index = 0; index < 100; index += 1) state = stepGame(state, 1, 0.05);
    expect(state.playerY).toBe(3.2);
  });

  it("reflects a ball that intersects the player paddle", () => {
    const state = { ...createInitialState(), ball: { x: 0, y: 0, z: -5.15 }, velocity: { x: 0, y: 0, z: -5 } };
    expect(stepGame(state, 0, 0.02).velocity.z).toBeGreaterThan(0);
  });

  it("awards the AI when the player misses", () => {
    const state = { ...createInitialState(), playerY: 3, ball: { x: 0, y: -3, z: -6 }, velocity: { x: 0, y: 0, z: -5 } };
    expect(stepGame(state, 0, 0.05).aiScore).toBe(1);
  });
});
'''


def _game_scene() -> str:
    return '''import * as THREE from "three";

import type { GameState } from "./physics";

export type GameScene = {
  render: (state: GameState) => void;
  dispose: () => void;
};

export function createGameScene(container: HTMLElement): GameScene {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x02050b);
  scene.fog = new THREE.Fog(0x02050b, 10, 28);
  const camera = new THREE.PerspectiveCamera(54, 1, 0.1, 100);
  camera.position.set(8.5, 7.2, 12.5);
  camera.lookAt(0, 0, 0);
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.domElement.setAttribute("aria-label", "Playable 3D Pong arena");
  container.appendChild(renderer.domElement);

  scene.add(new THREE.HemisphereLight(0x8de8ff, 0x10152a, 2.4));
  const keyLight = new THREE.PointLight(0xff4d8d, 65, 28);
  keyLight.position.set(0, 5, 4);
  scene.add(keyLight);

  const courtGeometry = new THREE.BoxGeometry(10, 7, 12);
  const court = new THREE.LineSegments(
    new THREE.EdgesGeometry(courtGeometry),
    new THREE.LineBasicMaterial({ color: 0x29d7f2, transparent: true, opacity: 0.45 })
  );
  scene.add(court);
  const centerLine = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-5, 0, 0), new THREE.Vector3(5, 0, 0)]),
    new THREE.LineDashedMaterial({ color: 0xffffff, dashSize: 0.3, gapSize: 0.25, transparent: true, opacity: 0.35 })
  );
  centerLine.computeLineDistances();
  scene.add(centerLine);

  const paddleGeometry = new THREE.BoxGeometry(2.4, 2.5, 0.35);
  const player = new THREE.Mesh(paddleGeometry, new THREE.MeshStandardMaterial({ color: 0x62f2ff, emissive: 0x075b6e }));
  const ai = new THREE.Mesh(paddleGeometry, new THREE.MeshStandardMaterial({ color: 0xff4d8d, emissive: 0x6b0d34 }));
  player.position.z = -5.2;
  ai.position.z = 5.2;
  scene.add(player, ai);

  const ball = new THREE.Mesh(
    new THREE.SphereGeometry(0.34, 24, 16),
    new THREE.MeshStandardMaterial({ color: 0xffe57a, emissive: 0x7a4f00, roughness: 0.22 })
  );
  scene.add(ball);

  const resize = () => {
    const width = Math.max(container.clientWidth, 1);
    const height = Math.max(container.clientHeight, 1);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  };
  const observer = new ResizeObserver(resize);
  observer.observe(container);
  resize();

  return {
    render: (state) => {
      player.position.y = -state.playerY;
      ai.position.y = -state.aiY;
      ball.position.set(state.ball.x, -state.ball.y, state.ball.z);
      ball.rotation.x += 0.025;
      ball.rotation.y += 0.035;
      renderer.render(scene, camera);
    },
    dispose: () => {
      observer.disconnect();
      courtGeometry.dispose();
      paddleGeometry.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    }
  };
}
'''


def _web_globals() -> str:
    return """* { box-sizing: border-box; }
html, body { margin: 0; min-height: 100%; background: #050713; color: #f8fbff; font-family: Arial, Helvetica, sans-serif; overflow: hidden; }
button, input { font: inherit; }
.game-shell { min-height: 100vh; display: grid; grid-template-rows: auto 1fr auto; padding: 18px; gap: 14px; background: radial-gradient(circle at 50% 20%, rgba(98,242,255,.18), transparent 34%), #050713; }
.hud { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.hud p { margin: 0; color: #62f2ff; font-size: 12px; letter-spacing: .14em; }
.hud h1 { margin: 4px 0 0; font-size: clamp(34px, 6vw, 72px); line-height: 1; }
.status { border: 1px solid rgba(98,242,255,.45); border-radius: 8px; padding: 10px 14px; color: #f8d14a; background: rgba(5,7,19,.65); }
.arena { width: 100%; height: 100%; min-height: 360px; border: 1px solid rgba(98,242,255,.3); border-radius: 8px; background: #050713; box-shadow: 0 20px 80px rgba(0,0,0,.4); touch-action: none; overflow: hidden; }
.arena canvas { display: block; width: 100%; height: 100%; }
.score { display: grid; grid-template-columns: 64px minmax(120px, 1fr) 64px; align-items: center; gap: 10px; text-align: center; }
.score strong { font-size: 32px; color: #62f2ff; }
.score span { color: #f8d14a; font-size: 12px; }
.actions { display: flex; gap: 8px; }
.actions button { border: 1px solid #62f2ff; border-radius: 6px; padding: 8px 12px; background: #07111e; color: #f8fbff; cursor: pointer; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; color: #9fb6d6; font-size: 13px; }
.controls span { border: 1px solid rgba(255,255,255,.14); border-radius: 999px; padding: 8px 10px; background: rgba(255,255,255,.04); }
@media (max-width: 760px) { .hud { align-items: flex-start; flex-wrap: wrap; } .arena { min-height: 55vh; } }
"""


def _web_e2e() -> str:
    return """import { expect, test } from "@playwright/test";

test("loads playable pong arena", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("3D PONG ARENA")).toBeVisible();
  const canvas = page.locator("canvas[aria-label='Playable 3D Pong arena']");
  await expect(canvas).toBeVisible();
  await expect(page.getByRole("button", { name: "Pause" })).toBeVisible();
});
"""


def _desktop_package(title: str) -> str:
    return f"""{{
  "name": "generated-3d-pong-desktop",
  "version": "0.1.0",
  "private": true,
  "main": "src/main.js",
  "scripts": {{
    "package": "echo Desktop wrapper scaffold for {title}"
  }}
}}
"""


def _desktop_main(title: str) -> str:
    return f"""console.log("{title} desktop wrapper scaffold");
"""


def _schema_sql() -> str:
    return """CREATE TABLE IF NOT EXISTS game_scores (
  id SERIAL PRIMARY KEY,
  player_score INTEGER NOT NULL,
  ai_score INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def _spec(idea: str) -> str:
    return f"""# 3D Pong Arena Spec

Prompt:

```text
{idea}
```

## Acceptance Criteria

- Render a playable Pong arena, not a SaaS dashboard.
- Show player and AI scores.
- Provide AI opponent movement.
- Support keyboard and pointer controls.
- Provide pause and restart.
- First player to 7 wins.
"""


def _architecture() -> str:
    return """# Architecture

The game is implemented as a Next.js client-rendered canvas experience. The API is intentionally minimal and provides health checks for Docker orchestration. Gameplay runs locally in the browser animation loop.
"""


def _security_doc() -> str:
    return """# Security

No secrets are required for local gameplay. The app does not collect user data by default.
"""


def _start_script() -> str:
    return """$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\\..
docker compose up --build
"""


def _test_script() -> str:
    return """$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\\..
docker compose run --rm api pytest -q
docker compose run --rm web npm run build
"""


def _package_windows_script() -> str:
    return """$ErrorActionPreference = "Stop"
Write-Host "Desktop package scaffold present. Use the web game at http://localhost:13000."
"""
