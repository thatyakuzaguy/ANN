export type Controls = {
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
