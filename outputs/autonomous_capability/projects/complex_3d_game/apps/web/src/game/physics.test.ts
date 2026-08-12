import { describe, expect, it } from "vitest";

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
