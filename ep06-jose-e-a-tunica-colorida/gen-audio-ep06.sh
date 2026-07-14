#!/bin/zsh
# EP06 José e a Túnica Colorida — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep06-jose-e-a-tunica-colorida
NARR=RGymW84CSmfVugnA5tvA
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar a história de José e a sua túnica colorida. Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[warm] O José tinha muitos irmãos. E o papai dele, Jacó, amava muito o José. [happy] Um dia, o papai deu para ele um presente lindo: uma túnica colorida!"
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[calm] Mas os irmãos ficaram com ciúme de José. [gentle] E José contou dois sonhos que teve. No primeiro sonho, os feixes de trigo dos irmãos se curvavam para o feixe dele. [awe] E no segundo sonho, o sol, a lua e onze estrelas se curvavam para José! [softly] Aí o ciúme ficou maior ainda."
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[calm] Um dia, longe de casa, os irmãos fizeram uma coisa muito errada. [somber] Tiraram a túnica colorida de José... e deixaram ele num poço fundo. [softly] Depois, mostraram a túnica para o papai Jacó e mentiram: Um bicho pegou o José! [somber] Mas José estava vivo. Os irmãos tinham vendido o irmão para uns moços que viajavam para bem longe, para o Egito. [softly] José foi embora sozinho. Que tristeza."
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[warm] Mas escuta só: Deus estava com José. Sempre! [calm] No Egito, José cresceu, e tudo o que ele fazia dava certo. [awe] O tempo passou, e o rei do Egito teve sonhos que ninguém entendia. E Deus mostrou para José o que os sonhos queriam dizer! [happy] O rei ficou tão feliz que fez de José um grande ajudante, o governador do Egito!"
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[calm] Então veio um tempo sem comida nas terras. E adivinha quem chegou no Egito procurando comida? [gentle] Os irmãos de José! [softly] José podia ficar bravo com eles, não podia? [warm] Mas José escolheu perdoar. Ele abraçou os irmãos e disse: Deus me mandou na frente, para salvar vidas."
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[happy] E José mandou buscar o papai Jacó! [warm] Quando se encontraram, José abraçou o papai e chorou de alegria. A família estava junta de novo."
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: Deus está com a gente, até bem longe de casa.

[calm] Dois: Deus pode transformar o mal em bem.

[warm] Três: perdoar faz a família ficar junta de novo.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."

py sfx --force --out $EP/sfx/tcham-presente.mp3 --duration 2.5 --prompt "magical cheerful gift reveal shimmer, cute sparkle chime flourish for a preschool show, bright and warm, no voices"
echo "AUDIO_EP06_DONE"
