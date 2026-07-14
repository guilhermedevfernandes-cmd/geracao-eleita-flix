#!/bin/zsh
# EP10 O Batismo de Jesus — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep10-o-batismo-de-jesus
NARR=RGymW84CSmfVugnA5tvA
DEUS=7i7dgyCkKt4c16dLtwT3
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar o dia em que Jesus foi batizado no rio. Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[calm] Naquele tempo, vivia um homem chamado João. Ele morava no deserto, usava uma roupa de pelos de camelo e comia mel silvestre. [warm] João avisava o povo: preparem o coração! Deus está chegando pertinho! [happy] E muitas pessoas vinham ouvir, e João as batizava no rio Jordão."
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[calm] E João sempre dizia: [awe] depois de mim, vem alguém muito mais importante do que eu. Eu não sou digno nem de carregar as sandálias dele!"
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[awe] Um dia, Jesus veio da Galileia até o rio Jordão. [warm] Quando João viu Jesus chegando, ficou muito feliz e disse: olhem! É o Cordeiro de Deus!"
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[gentle] Jesus pediu para João batizá-lo. Mas João disse: eu é que preciso ser batizado por você! [calm] E Jesus respondeu: deixa assim por agora. É isso que Deus quer que a gente faça. [warm] E João obedeceu."
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[calm] Então João batizou Jesus no rio Jordão. [softly] A aguinha brilhou... e Jesus saiu da água."
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[awe] E aí aconteceu uma coisa linda: o céu se abriu! [warm] E o Espírito de Deus desceu sobre Jesus, suavinho, como uma pombinha. [calm] E lá do céu, veio a voz de Deus:"
py tts --force --voice-id $DEUS --out $EP/audio/c7_1.mp3 --text "[warm] Este é o meu Filho amado. Nele eu me alegro muito!"
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: Jesus obedeceu a Deus em tudo, desde o começo.

[calm] Dois: Deus, o Papai do céu, ama muito o Filho dele, Jesus.

[warm] Três: quem anda com Jesus deixa Deus muito alegre.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."
echo "AUDIO_EP10_DONE"
