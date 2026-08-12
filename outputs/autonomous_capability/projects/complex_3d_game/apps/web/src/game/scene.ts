import * as THREE from "three";

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
