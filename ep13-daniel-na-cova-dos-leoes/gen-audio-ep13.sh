#!/bin/zsh
# EP13 Daniel na Cova dos Leões — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
# Narração toda pela narradora (falas do rei e de Daniel citadas por ela, como no EP12).
set -eu
cd "${0:A:h:h}"
EP=ep13-daniel-na-cova-dos-leoes
NARR=RGymW84CSmfVugnA5tvA
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar a história de Daniel. Ele já era bem velhinho, tinha cabelos brancos... e amou a Deus a vida inteira. Vem comigo!"
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[calm] Na terra da Babilônia, vivia o rei Dario. Ele escolheu muitos líderes para cuidar do reino. [warm] E o melhor de todos era Daniel. Deus tinha dado muita sabedoria a ele. [happy] Por isso, o rei quis colocar Daniel como chefe de todo o reino."
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[calm] Sabe o que Daniel fazia todos os dias? Três vezes por dia, ele abria a janela, ficava de joelhos... e orava, agradecendo a Deus. [warm] Ele fazia isso desde sempre. Você também gosta de conversar com Deus?"
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[calm] Mas alguns homens do palácio ficaram com inveja de Daniel. Eles procuraram algum erro nele... e não acharam nenhum! [gentle] Então armaram um plano que não era bom. Disseram ao rei: Ó rei, faça uma lei! Por trinta dias, ninguém pode orar a ninguém, só ao rei! [calm] E o rei assinou a lei, sem saber que era uma armadilha."
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[calm] O Daniel ficou sabendo da lei. E o que ele fez? [warm] Foi para casa, abriu a janela na direção de Jerusalém, ficou de joelhos... e orou a Deus, como sempre fazia. [gentle] Mas os homens invejosos estavam espiando. E correram para contar ao rei."
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[gentle] O rei ficou muito triste, porque gostava de Daniel. Ele tentou salvá-lo o dia inteiro... mas aquela lei não podia mudar. [calm] Então Daniel foi colocado na cova dos leões. E o rei disse: Que o seu Deus, a quem você serve todos os dias, livre você dos leões! [gentle] Uma pedra enorme fechou a entrada. E o rei passou a noite inteira sem comer e sem dormir, preocupado."
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[awe] Dentro da cova, havia leões enormes. Roooar! [calm] Mas Daniel não ficou sozinho: Deus enviou o seu anjo, e o anjo fechou a boca dos leões. [gentle] De manhã, bem cedo, o rei correu até a cova e chamou: Daniel! O seu Deus pôde livrar você? [happy] E Daniel respondeu: Ó rei, o meu Deus enviou o seu anjo e fechou a boca dos leões! Eles não me machucaram. [warm] Daniel saiu da cova sem nenhum arranhão, porque confiou no seu Deus."
py tts --force --voice-id $NARR --out $EP/audio/c8_0.mp3 --text "[happy] O rei ficou tão feliz! E mandou avisar o reino inteiro: O Deus de Daniel é o Deus vivo! Ele livra e salva o seu povo."
py tts --force --voice-id $NARR --out $EP/audio/c9_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: podemos orar a Deus todos os dias, como Daniel orava.

[calm] Dois: Deus enviou o seu anjo e cuidou de Daniel na cova.

[warm] Três: o Deus de Daniel é o Deus vivo, que livra e salva.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."

py sfx --force --out $EP/sfx/pedra-arrastando.mp3 --duration 4 --prompt "a big round stone slowly rolling and grinding over stone to seal a cave entrance, soft and gentle for a preschool cartoon, low rumble, not scary, no voices"
py sfx --force --out $EP/sfx/leao-rugido-fofo.mp3 --duration 3 --prompt "a friendly gentle lion soft roar for a cute preschool cartoon, warm and rounded, playful not scary, no music, no voices"
echo "AUDIO_EP13_DONE"
