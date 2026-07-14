#!/bin/zsh
# EP04 Caim e Abel — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep04-caim-e-abel
NARR=RGymW84CSmfVugnA5tvA
DEUS=7i7dgyCkKt4c16dLtwT3
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar a história de dois irmãos: Caim e Abel. Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[warm] Depois que saíram do jardim, Adão e Eva tiveram dois filhos. [happy] Caim, o mais velho, plantava comidinhas na terra. E Abel, o mais novo, cuidava das ovelhinhas."
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[calm] Um dia, os dois trouxeram presentes para Deus. Caim trouxe frutos da sua plantação. E Abel trouxe as primeiras ovelhinhas do seu rebanho, as melhores."
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[calm] Deus se agradou do presente de Abel. [gentle] Mas do presente de Caim, não. [softly] E Caim ficou com muita raiva. Ficou de cara fechada, emburrado."
py tts --force --voice-id $DEUS --out $EP/audio/c5_0.mp3 --text "[calm] Caim, por que você está com raiva? Se você fizer o bem, tudo vai ficar bem. Mas cuidado: o pecado está na sua porta, querendo te pegar. Você precisa vencer ele."
py tts --force --voice-id $NARR --out $EP/audio/c5_1.mp3 --text "[gentle] Deus avisou Caim com carinho. Mas Caim não quis ouvir."
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[calm] Um dia, Caim chamou Abel para ir ao campo. [somber] E lá, com muita raiva no coração, Caim machucou o seu irmão. E Abel morreu. [softly] Foi muito, muito triste."
py tts --force --voice-id $DEUS --out $EP/audio/c7_0.mp3 --text "[calm] Caim, onde está Abel, o seu irmão?"
py tts --force --voice-id $NARR --out $EP/audio/c7_1.mp3 --text "[calm] E Caim respondeu: [curious] Não sei! Sou eu que cuido do meu irmão?? [gentle] Mas Deus sabia de tudo. Deus vê tudo."
py tts --force --voice-id $NARR --out $EP/audio/c8_a.mp3 --text "[calm] Por causa do que fez, Caim recebeu um castigo: teve que ir morar bem longe. [gentle] Para sempre, longe da sua família."
py tts --force --voice-id $NARR --out $EP/audio/c8_b.mp3 --text "[gentle] Mas olha só: mesmo assim, Deus colocou um sinal em Caim, para ninguém machucar ele. [warm] Mesmo quando a gente erra feio, Deus continua cuidando."
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: Deus vê tudo, até o nosso coração.

[calm] Dois: quando a raiva chegar, precisamos vencer ela, fazendo o bem.

[warm] Três: mesmo quando erramos, Deus continua cuidando da gente.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."

# SFX novos
py sfx --force --out $EP/sfx/vento-triste.mp3 --duration 4 --prompt "soft gentle melancholic cartoon wind whoosh for a preschool show, tender, airy, nothing scary, no voices"
py sfx --force --out $EP/sfx/vento-suave.mp3 --duration 4 --prompt "very light gentle breeze whoosh, soft cartoon wind for toddlers, calm and cozy, no voices"
py sfx --force --out $EP/sfx/whoosh-suave.mp3 --duration 2 --prompt "tiny soft comedic deflating whoosh, cute cartoon disappointed puff, gentle, for preschool animation, no voices"
echo "AUDIO_EP04_DONE"
