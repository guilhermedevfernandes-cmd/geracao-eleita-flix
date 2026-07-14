#!/bin/zsh
# EP12 Moisés e o Mar Vermelho — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep12-moises-e-o-mar-vermelho
NARR=RGymW84CSmfVugnA5tvA
DEUS=7i7dgyCkKt4c16dLtwT3
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar a história de Moisés. Lembra do bebê da cestinha? Ele cresceu! Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[calm] O Moisés cresceu no palácio do Egito. Mas o povo dele, o povo de Deus, trabalhava sem parar, e sofria muito. [gentle] Um dia, Moisés foi morar bem longe, e virou pastor de ovelhinhas."
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[awe] Um dia, no monte, Moisés viu uma coisa incrível: um arbusto pegando fogo... que não queimava! E dali, Deus chamou:"
py tts --force --voice-id $DEUS --out $EP/audio/c3_1.mp3 --text "[calm] Moisés! Moisés! Tire as sandálias, porque este lugar é santo. [warm] Eu vi o sofrimento do meu povo no Egito. Vá até o Faraó... e tire o meu povo de lá!"
py tts --force --voice-id $NARR --out $EP/audio/c3_2.mp3 --text "[gentle] E Moisés obedeceu. Ele foi."
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[calm] Moisés chegou ao palácio do Faraó e disse: Assim diz o Senhor: deixa o meu povo ir! [gentle] Mas o Faraó disse: Não! [awe] Então Deus mandou muitos sinais, um atrás do outro... [happy] até que o Faraó deixou! E o povo de Deus saiu do Egito."
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[calm] Mas o Faraó mudou de ideia, e mandou os soldados atrás do povo. [gentle] E na frente deles... o mar! Um mar grandão. O povo ficou com medo. [warm] Mas Moisés disse: Não tenham medo! O Senhor vai lutar por vocês!"
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[calm] E Deus falou com Moisés:"
py tts --force --voice-id $DEUS --out $EP/audio/c6_1.mp3 --text "[calm] Levante o seu cajado sobre o mar."
py tts --force --voice-id $NARR --out $EP/audio/c6_2.mp3 --text "[awe] Moisés levantou o cajado... e Deus mandou um vento bem forte. E o mar se abriu! Duas paredes de água, e um caminho seco no meio! [happy] E todo o povo atravessou."
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[calm] Quando os soldados tentaram passar, o mar voltou. Splash! [happy] E o povo de Deus estava seguro do outro lado. [warm] Todo mundo cantou e dançou de alegria, agradecendo a Deus. A Miriã, irmã de Moisés, dançou com o seu pandeiro!"
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: Deus ouve o choro do seu povo.

[calm] Dois: Deus abre caminho onde não tem caminho.

[warm] Três: quem confia em Deus não precisa ter medo.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."

py sfx --force --out $EP/sfx/fogo-crepitar.mp3 --duration 4 --prompt "soft magical gentle campfire crackle for a preschool cartoon, warm and cozy, sacred glow shimmer, no voices, not scary"
echo "AUDIO_EP12_DONE"
