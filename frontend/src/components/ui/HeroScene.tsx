import { useEffect, useRef } from "react";

/**
 * Cena Three.js decorativa: uma rede de "produtos" (nós) ligados por "regras" (arestas),
 * metáfora visual do grafo de associações do Apriori. Carregada sob demanda (chunk separado).
 */
export function HeroScene() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let disposed = false;
    let cleanup = () => {};

    import("three").then((THREE) => {
      if (disposed) return;
      let renderer: InstanceType<typeof THREE.WebGLRenderer>;
      try {
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      } catch {
        return; // sem WebGL: a cena é apenas decorativa
      }
      const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(50, el.clientWidth / el.clientHeight, 0.1, 100);
      camera.position.z = 9;
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(el.clientWidth, el.clientHeight);
      el.appendChild(renderer.domElement);

      const group = new THREE.Group();
      scene.add(group);
      // Posições determinísticas (pseudoaleatório com semente fixa).
      let s = 42;
      const rand = () => ((s = (s * 16807) % 2147483647) / 2147483647) * 2 - 1;
      const nodes = Array.from({ length: 26 }, () => new THREE.Vector3(rand() * 4, rand() * 3, rand() * 3));
      const nodeGeo = new THREE.IcosahedronGeometry(0.16, 1);
      const colors = [0x8b5cf6, 0x22d3ee, 0xec4899];
      const materials = colors.map((c) => new THREE.MeshBasicMaterial({ color: c }));
      nodes.forEach((p, i) => {
        const m = new THREE.Mesh(nodeGeo, materials[i % 3]);
        m.position.copy(p);
        group.add(m);
      });
      const pts: number[] = [];
      nodes.forEach((a, i) => nodes.forEach((b, j) => {
        if (j > i && a.distanceTo(b) < 2.4) pts.push(a.x, a.y, a.z, b.x, b.y, b.z);
      }));
      const lineGeo = new THREE.BufferGeometry();
      lineGeo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
      const lineMat = new THREE.LineBasicMaterial({ color: 0x6d5bd0, transparent: true, opacity: 0.55 });
      group.add(new THREE.LineSegments(lineGeo, lineMat));

      let frame = 0;
      const render = () => {
        group.rotation.y += 0.0025;
        group.rotation.x = Math.sin(Date.now() / 4000) * 0.15;
        renderer.render(scene, camera);
        frame = requestAnimationFrame(render);
      };
      if (reduceMotion) renderer.render(scene, camera);
      else render();

      const onResize = () => {
        camera.aspect = el.clientWidth / el.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(el.clientWidth, el.clientHeight);
        if (reduceMotion) renderer.render(scene, camera);
      };
      window.addEventListener("resize", onResize);

      cleanup = () => {
        cancelAnimationFrame(frame);
        window.removeEventListener("resize", onResize);
        nodeGeo.dispose(); lineGeo.dispose(); lineMat.dispose();
        materials.forEach((m) => m.dispose());
        renderer.dispose();
        renderer.domElement.remove();
      };
    });

    return () => { disposed = true; cleanup(); };
  }, []);

  return <div ref={ref} className="hero__canvas" aria-hidden="true" />;
}
