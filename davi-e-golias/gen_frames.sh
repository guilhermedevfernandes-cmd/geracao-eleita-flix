#!/bin/zsh
# Gera frames das cenas via nano_banana_2 com referência de personagem.
# Uso: ./gen_frames.sh <n_inicial> <n_final>
set -u
cd "$(dirname "$0")"
DAVI=1f4165b4-e8ea-4c4c-8f37-5c0f79677c59
GOLIAS=81b0849f-47ae-41b4-a6a9-c773e4cb58e6
STYLE="Disney Pixar 3D animation style, soft cinematic lighting, warm color palette, family-friendly, highly detailed, 16:9"
mkdir -p frames

gen() {
  local n=$1; shift
  local refs=$1; shift
  local prompt=$1
  local nn=$(printf "%02d" $n)
  echo "=== Cena $nn (ref: ${refs:-nenhuma}) ==="
  local imgargs=()
  [[ "$refs" == *D* ]] && imgargs+=(--image $DAVI)
  [[ "$refs" == *G* ]] && imgargs+=(--image $GOLIAS)
  local url
  url=$(higgsfield generate create nano_banana_2 \
    --prompt "$prompt, $STYLE" \
    "${imgargs[@]}" \
    --aspect_ratio 16:9 --resolution 2k --wait --wait-timeout 8m 2>&1 | tail -1)
  if [[ "$url" == http* ]]; then
    curl -s -o "frames/${nn}.png" "$url" && echo "  ✓ frames/${nn}.png"
  else
    echo "  ✗ FALHOU: $url"
  fi
}

S=${1:-1}; E=${2:-16}

run() {
  case $1 in
  1) gen 1 "" "Wide aerial establishing shot of a lush green valley between two hills at golden hour, two ancient armies camped on opposite sides with colorful tents and banners, epic but gentle" ;;
  2) gen 2 "G" "The same giant Philistine warrior Goliath from the reference (bronze scale armor, helmet, dark beard), standing huge over tiny soldiers, dramatic low-angle, towering silhouette" ;;
  3) gen 3 "G" "Goliath from the reference shouting with a big confident grin, hands cupped around his mouth, cartoon shockwave rings of sound, frightened tiny soldiers covering their ears" ;;
  4) gen 4 "" "King Saul, a worried middle-aged king with a golden crown and royal robe, sitting on a small throne inside a tent looking pale and anxious, trembling soldiers around him, soft fearful expressions" ;;
  6) gen 6 "D" "David from the reference standing next to an old kind father with a gray beard who hands him a basket of bread, near a stone house, warm morning light, loving expressions" ;;
  7) gen 7 "D" "David from the reference walking into a busy military camp with tents and soldiers, looking up surprised, a giant warrior roaring far in the background" ;;
  8) gen 8 "D" "Close-up of David from the reference with brave determined eyes and clenched fists, soft warm glow of courage around him, ashamed soldiers blurred behind" ;;
  9) gen 9 "D" "Small David from the reference standing bravely before a surprised King Saul (golden crown, royal robe) who raises his eyebrows in disbelief, throne tent interior, warm light" ;;
  10) gen 10 "D" "David from the reference standing protectively between his white sheep and a cartoon lion and a cartoon bear, brave pose, gentle non-scary danger, golden field" ;;
  11) gen 11 "D" "Tiny David from the reference wearing an oversized heavy bronze armor and a too-big helmet, wobbling comically, King Saul watching with a smile, lighthearted" ;;
  12) gen 12 "D" "David from the reference kneeling by a sparkling stream picking up five smooth stones, holding a leather sling, sunlight glinting on the water, calm determined face" ;;
  13) gen 13 "DG" "The huge giant Goliath from the reference laughing down at tiny brave David from the reference standing firm in the valley, dramatic size contrast, two armies watching in the background" ;;
  14) gen 14 "D" "David from the reference running forward and spinning his leather sling overhead, motion blur arc, a small stone with a light trail, dynamic action pose" ;;
  15) gen 15 "G" "The giant Goliath from the reference falling backward dramatically with cartoon stars and a puff of dust, surprised dizzy expression, a tiny shepherd boy standing victorious in the background, gentle comedic impact" ;;
  16) gen 16 "D" "A joyful crowd of Israelite soldiers cheering and lifting young David from the reference up as a hero, sparkles of light like confetti, a sunset rainbow over the valley, celebration" ;;
  5) echo "=== Cena 05 já existe, pulando ===" ;;
  esac
}

for ((i=S; i<=E; i++)); do run $i; done
echo "=== concluído $S..$E ==="
