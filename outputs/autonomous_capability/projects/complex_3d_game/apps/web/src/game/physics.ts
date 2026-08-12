export type Winner = "player" | "ai" | null;

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
