#!/bin/zsh
# EP09 O Nascimento de Jesus — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep09-o-nascimento-de-jesus
NARR=RGymW84CSmfVugnA5tvA
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar a história mais linda de todas: o nascimento do bebê Jesus. Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[calm] Naquele tempo, o rei mandou que todo mundo fosse se registrar na cidade da sua família. [warm] Por isso, José e Maria viajaram para Belém. [softly] E a Maria estava esperando um bebê... o bebê Jesus."
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[gentle] Quando chegaram, as casinhas de hóspedes estavam cheias. Não havia lugar para eles. [calm] Então eles ficaram num cantinho aconchegante, onde os animais dormiam. [softly] E chegou a hora do bebê nascer."
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[awe] E ali, naquela noite... nasceu Jesus! [warm] Maria enrolou o bebê em paninhos, bem quentinho, e o deitou numa manjedoura, a caminha de feno dos animais. [awe] O nosso Salvador nasceu! [softly] O bebê mais esperado de todos os tempos."
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[calm] Perto dali, alguns pastores cuidavam das ovelhinhas na noite. [awe] De repente, um anjo do Senhor apareceu, e uma luz linda brilhou! Eles ficaram com muito medo. [warm] Mas o anjo disse: não tenham medo! Eu trago uma notícia de muita alegria: hoje nasceu o Salvador de vocês, o Cristo, o Senhor! Vocês vão encontrar o bebê deitado numa manjedoura."
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[awe] E de repente, o céu se encheu de anjos, uma multidão! [happy] E todos cantavam louvando a Deus: glória a Deus nas alturas, e paz na terra!"
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[happy] Os pastores correram para Belém... e encontraram Maria, José e o bebê deitado na manjedoura, do jeitinho que o anjo falou! [warm] Eles contaram tudo o que tinham visto. [calm] E depois voltaram para casa louvando a Deus por tudo."
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: Jesus é o presente de Deus para nós.

[calm] Dois: Deus conta as boas notícias até para os mais simples, como os pastores.

[warm] Três: quando conhecemos Jesus, louvamos a Deus de alegria.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."
echo "AUDIO_EP09_DONE"
