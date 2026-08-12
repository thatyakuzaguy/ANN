"use client";

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
