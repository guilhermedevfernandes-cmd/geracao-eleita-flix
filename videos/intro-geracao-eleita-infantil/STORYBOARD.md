---
compositionId: intro-geracao-eleita
mode: autonomous
duration_s: 6.0
canvas: { "w": 1920, "h": 1080, "fps": 30 }
style:
  font: "Fredoka One"
  palette: ["#F5F0E6", "#7ECDC0", "#FDE68A", "#D4A5E8", "#F8635F", "#2D2D2D"]
assets: "4 personagens 3D infantis animados em assets/characters"
build_notes:
  - "uma cena 3D deterministica dirigida pelo tempo do HyperFrames"
  - "AnimationMixer.setTime para cada GLB"
  - "fontes e modelos locais; sem assets remotos em tempo de render"
  - "terminar no lockup colorido, nunca em preto"
avoid:
  - "realismo fotografico"
  - "sombras borradas"
  - "movimento agressivo ou assustador"
  - "texto pequeno"
---

## Frame 1 — intro

- src: compositions/frames/01-intro.html
- duration: 6.0s
- span_sec: [0.0, 6.0]
- pacing: beat_cut
- mood: [warm, playful, dreamy]
- feel: silêncio inicial de 1s, duas subidas em 1s e 2s, seção densa com fill de 3.04s a 4.06s e parada forte em 5s

### Groups

- **g1** — free_design
  - span_sec: [0.0, 6.0]
  - free_design: { dominant_system: "tableau 3D infantil com Jesus ao centro e três crianças ao redor", primitives: ["iris-open", "braam-punch", "particle-burst", "freeze-hold"], density_topology: "silêncio visual → revelação → celebração → lockup" }
  - anchors: [0.05, 0.19, 0.63, 1.0, 1.07, 1.72, 2.0, 2.35, 3.04, 3.46, 4.06, 4.55, 5.0, 5.2, 5.41, 5.8]
  - copy: ["GERAÇÃO", "ELEITA"]
  - assets: ["assets/characters/jesus-idle.glb", "assets/characters/crianca-01-celebration.glb", "assets/characters/crianca-02-rigged.glb", "assets/characters/crianca-03-celebration.glb"]
