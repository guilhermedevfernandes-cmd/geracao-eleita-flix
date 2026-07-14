#!/bin/zsh
set -u
cd "$(dirname "$0")"
JOAO=e878162d-228f-43d0-832d-9c5a0b0ad394
JESUS=e11a3248-36a0-4494-a562-fc30ba7f9905
STYLE="Disney Pixar 3D animation style, soft cinematic lighting, warm color palette, expressive big eyes, family-friendly, highly detailed, 16:9"
mkdir -p frames

gen() {
  local n=$1; shift; local refs=$1; shift; local prompt=$1
  local nn=$(printf "%02d" $n)
  echo "=== Cena $nn (ref: ${refs:-nenhuma}) ==="
  local a=()
  [[ "$refs" == *J* ]] && a+=(--image $JOAO)
  [[ "$refs" == *S* ]] && a+=(--image $JESUS)
  local url
  url=$(higgsfield generate create nano_banana_2 --prompt "$prompt, $STYLE" "${a[@]}" \
        --aspect_ratio 16:9 --resolution 2k --wait --wait-timeout 8m 2>&1 | tail -1)
  [[ "$url" == http* ]] && curl -s -o "frames/${nn}.png" "$url" && echo "  ✓ frames/${nn}.png" || echo "  ✗ $url"
}

S=${1:-1}; E=${2:-16}
run() { case $1 in
1) gen 1 "" "Inside an ancient golden temple, an old kind priest named Zacarias with a long white beard and priestly robe kneeling in prayer, startled as a tall glowing angel with soft white wings appears in warm radiant light, sacred peaceful atmosphere" ;;
2) gen 2 "" "An old priest Zacarias with a long white beard standing speechless with his hand over his mouth, eyes wide in surprise, soft golden light fading around him, other temple priests looking puzzled in the background, ancient temple interior" ;;
3) gen 3 "" "An old gentle woman named Isabel with a soft smile and a headscarf, hands resting happily on her pregnant belly, standing in a cozy warm stone house with sunlight through a window, joyful peaceful mood" ;;
4) gen 4 "" "An old priest Zacarias with white beard joyfully writing on a small wooden tablet, a newborn baby wrapped in cloth nearby, an old woman Isabel beside him smiling, family and neighbors celebrating in a warm candlelit home, tender joyful scene" ;;
5) gen 5 "" "A young boy around 10 years old with curly dark hair in a simple tunic, happily walking through a warm golden desert landscape with rocks and small bushes, clear blue sky, peaceful and adventurous" ;;
6) gen 6 "J" "John the Baptist from the reference as a grown man in his camel-hair tunic and leather belt, standing strong on a desert hill at golden hour holding his wooden staff, a small honeycomb nearby, vast warm desert behind him, noble and humble" ;;
7) gen 7 "J" "John the Baptist from the reference standing by the wide Jordan river preaching passionately with an open hand, a large crowd of people of all ages gathered on the riverbank listening intently, green palm trees, warm sunlight on the water" ;;
8) gen 8 "J" "John the Baptist from the reference standing waist-deep in the clear Jordan river gently baptizing a smiling person, people waiting on the bank, sparkling water droplets, warm light, hopeful sacred mood" ;;
9) gen 9 "J" "John the Baptist from the reference speaking earnestly to the crowd, one hand pointing toward the horizon, golden light breaking through clouds in the distance, the crowd looking hopeful, dramatic but gentle inspiring atmosphere" ;;
10) gen 10 "JS" "Jesus from the second reference in his white robe walking calmly toward John the Baptist from the first reference at the edge of the Jordan river, soft glowing light around Jesus, the crowd watching quietly in wonder, warm serene atmosphere" ;;
11) gen 11 "JS" "John the Baptist from the first reference with a humble surprised expression gesturing gently, Jesus from the second reference smiling kindly and reassuring him, the two facing each other at the riverbank, soft golden light, tender respectful mood" ;;
12) gen 12 "JS" "John the Baptist from the first reference gently baptizing Jesus from the second reference in the clear Jordan river, both standing in the sparkling water, soft radiant light from above, the crowd watching in reverence, sacred beautiful moment" ;;
13) gen 13 "S" "The sky opening with radiant beams of light over the river, a glowing white dove descending gently toward Jesus from the reference who stands in the water looking up peacefully, magical sacred light, awe and wonder" ;;
14) gen 14 "S" "Jesus from the reference standing in the river bathed in warm heavenly light from above, a glowing white dove near him, the crowd on the bank kneeling in awe, golden radiant rays filling the sky, glorious gentle sacred scene" ;;
15) gen 15 "JS" "John the Baptist from the first reference smiling joyfully and pointing toward Jesus from the second reference who glows softly nearby at the river, the happy crowd looking on, warm golden sunset light, hopeful triumphant mood" ;;
16) gen 16 "J" "John the Baptist from the reference standing peacefully on a hill at golden sunset overlooking the Jordan river and the happy crowds, a warm glowing sky, a sense of peace and fulfillment, beautiful hopeful closing shot" ;;
esac }
for ((i=S; i<=E; i++)); do run $i; done
echo "=== concluído $S..$E ==="
