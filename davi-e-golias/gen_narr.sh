#!/bin/zsh
set -u
cd "$(dirname "$0")"
mkdir -p audio
VOICE=30fc8796-ceb6-4a66-b3a7-4a145ef7f346   # Arthur (male, warm)
gen() {
  local nn=$(printf "%02d" $1); shift
  local txt=$1
  echo "=== narr $nn ==="
  local url
  url=$(higgsfield generate create text2speech_v2 \
    --model elevenlabs --voice_id $VOICE --voice_type preset \
    --prompt "$txt" --wait --wait-timeout 5m 2>&1 | tail -1)
  if [[ "$url" == http* ]]; then
    curl -s -o "audio/${nn}.mp3" "$url"
    local d=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "audio/${nn}.mp3" 2>/dev/null)
    printf "  ✓ audio/%s.mp3  %.1fs\n" $nn $d
  else
    echo "  ✗ FALHOU: $url"
  fi
}
gen 2  "E entre os filisteus vivia um guerreiro gigante, chamado Golias. Ele era mais alto que três homens juntos!"
gen 3  "Todos os dias, Golias gritava bem alto: mandem alguém para lutar comigo, se tiverem coragem!"
gen 4  "Mas ninguém tinha coragem. Até o rei Saul tremia de medo só de ouvir aquela voz."
gen 5  "Longe dali, um menino pastor chamado Davi cuidava de suas ovelhas e tocava harpa com alegria."
gen 6  "Um dia, o pai de Davi pediu: leve estes pães para seus irmãos, que estão no acampamento."
gen 7  "Davi caminhou até o vale e chegou bem na hora em que Golias soltava seu grito assustador."
gen 8  "Davi não entendeu: por que ninguém enfrenta esse gigante? Deus está conosco!"
gen 9  "Então Davi foi até o rei e disse: eu vou lutar contra Golias! O rei Saul ficou espantado."
gen 10 "Eu já protegi minhas ovelhas de um leão e de um urso. Deus vai me ajudar de novo!"
gen 11 "Saul ofereceu sua armadura, mas era tão pesada que Davi quase não conseguia andar."
gen 12 "Davi tirou a armadura e escolheu cinco pedrinhas lisas no riacho. Só precisava da sua funda e de sua fé."
gen 13 "Golias riu ao ver o menino: você acha que pode me vencer? Mas Davi não teve medo."
gen 14 "Davi correu, girou a funda no ar com toda a força e lançou a pedra bem na hora certa."
gen 15 "A pedrinha acertou a testa de Golias, e o grande gigante caiu no chão com um baque!"
gen 16 "O povo de Israel comemorou! E todos aprenderam que, com fé e coragem, até o menor pode vencer."
echo "=== narração concluída ==="
