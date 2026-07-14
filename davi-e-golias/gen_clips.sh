#!/bin/zsh
# Anima cada frame em clipe de 8s via kling3_0 (mais tolerante p/ personagem infantil).
# Uso: ./gen_clips.sh <n_inicial> <n_final>
set -u
cd "$(dirname "$0")"
mkdir -p clips

gen() {
  local n=$1; shift
  local prompt=$1
  local nn=$(printf "%02d" $n)
  echo "=== Clip $nn ==="
  if [[ ! -f "frames/${nn}.png" ]]; then echo "  ✗ sem frame ${nn}"; return; fi
  local url
  url=$(higgsfield generate create kling3_0 \
    --prompt "$prompt. Disney Pixar 3D animation style, family-friendly." \
    --image "frames/${nn}.png" \
    --duration 8 --aspect_ratio 16:9 --mode std --sound off \
    --wait --wait-timeout 18m 2>&1 | tail -1)
  if [[ "$url" == http* ]]; then
    curl -s -o "clips/${nn}.mp4" "$url" && echo "  ✓ clips/${nn}.mp4"
  else
    echo "  ✗ FALHOU: $url"
  fi
}

S=${1:-1}; E=${2:-16}
run() {
  case $1 in
  1) gen 1 "Slow cinematic aerial drift over the green valley, banners and tent flags gently waving in the breeze, soft clouds moving, warm sunlight, calm establishing motion" ;;
  2) gen 2 "Slow low-angle camera tilt up revealing the giant warrior's full height, cape and banners flutter, tiny soldiers look up nervously, dramatic but gentle" ;;
  3) gen 3 "The giant shouts, mouth moving, comedic shockwave rings push outward, soldiers flinch back and cover their ears, slight camera shake, lighthearted" ;;
  4) gen 4 "The worried king nervously grips his throne, soldiers tremble and exchange worried glances, candle flames flicker, slow push-in on his anxious face" ;;
  5) gen 5 "The shepherd boy gently plays his harp, fingers moving, fluffy sheep graze, butterflies flutter, soft breeze moves grass and hair, slow cinematic push-in" ;;
  6) gen 6 "The old father hands the bread basket to the boy, both smile warmly, the boy nods, gentle morning light, soft natural motion" ;;
  7) gen 7 "The boy walks forward into the camp and stops, looking up surprised toward the distant giant, soldiers move around him, dynamic but calm" ;;
  8) gen 8 "Slow push-in on the boy's determined face, his expression hardens with courage, soft warm glow intensifies, hair moves slightly" ;;
  9) gen 9 "The boy speaks confidently with a small gesture, the king leans back surprised raising his eyebrows, gentle reaction, warm light" ;;
  10) gen 10 "The brave boy stands firm and raises his staff, the cartoon lion and bear back away playfully, sheep huddle safe behind him, brave heroic motion" ;;
  11) gen 11 "The small boy wobbles comically under the heavy oversized armor, the helmet slips over his eyes, he tilts side to side, the king chuckles, funny gentle motion" ;;
  12) gen 12 "The boy kneels and picks up a smooth stone from the sparkling stream, water ripples and glints, he stands and grips his sling, calm determined motion" ;;
  13) gen 13 "The giant laughs and points down mockingly, the tiny boy stands firm and unflinching looking up, wind moves the grass, dramatic gentle tension" ;;
  14) gen 14 "The boy runs forward and spins his sling fast overhead in a glowing circular blur then releases, the stone shoots forward with a light trail, dynamic energetic motion" ;;
  15) gen 15 "The giant stumbles, his eyes go dizzy with spinning cartoon stars, and he falls backward with a big soft dust puff, comedic gentle impact, the boy stands victorious" ;;
  16) gen 16 "The crowd cheers and lifts the boy up joyfully, confetti sparkles fall, a rainbow glows over the valley at sunset, triumphant happy motion, slow zoom out" ;;
  esac
}
for ((i=S; i<=E; i++)); do run $i; done
echo "=== concluído $S..$E ==="
