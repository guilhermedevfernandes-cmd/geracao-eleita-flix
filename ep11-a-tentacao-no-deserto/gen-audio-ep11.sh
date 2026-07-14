#!/bin/zsh
# EP11 A Tentação no Deserto — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep11-a-tentacao-no-deserto
NARR=RGymW84CSmfVugnA5tvA
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar o dia em que Jesus venceu o enganador, lá no deserto. Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[calm] Depois do batismo, o Espírito de Deus levou Jesus para o deserto. [awe] Lá, Jesus ficou quarenta dias sem comer, orando. [softly] Quarenta dias! No fim, ele estava com muita, muita fome."
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[calm] Foi aí que apareceu o enganador, o diabo. Ele queria que Jesus desobedecesse a Deus. [gentle] E disse: se você é o Filho de Deus, mande estas pedras virarem pães! [warm] Mas Jesus respondeu: está escrito: não é só de pão que a gente vive, mas de toda palavra que vem de Deus."
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[calm] Depois, o enganador levou Jesus até o ponto mais alto do templo. [gentle] E disse: se você é o Filho de Deus, pula daqui! Os anjos vão te segurar! [warm] Mas Jesus respondeu de novo: também está escrito: não ponha o Senhor seu Deus à prova."
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[calm] Por fim, o enganador levou Jesus a um monte bem alto e mostrou todos os reinos do mundo, brilhando. [gentle] E disse: tudo isso eu te dou... se você se ajoelhar e me adorar. [awe] Aí Jesus respondeu bem firme: sai daqui, Satanás! Está escrito: adore só ao Senhor seu Deus. Sirva só a Ele!"
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[happy] E sabe o que aconteceu? O enganador foi embora! Jesus venceu! [warm] E aí, anjos de Deus vieram cuidar de Jesus."
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[warm] Viu só? Todas as vezes, Jesus respondeu com a Palavra de Deus: está escrito! [calm] A Palavra de Deus é a nossa força contra o enganador."
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: o enganador quer nos afastar de Deus, mas Jesus é mais forte.

[calm] Dois: a Palavra de Deus é a nossa espada: está escrito!

[warm] Três: adore só a Deus, e sirva só a Ele.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."
echo "AUDIO_EP11_DONE"
