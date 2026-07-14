#!/bin/zsh
# v3 (12/07/2026): Eleven v3 + stability Robusto + AUDIO TAGS de expressão
# por segmento (workflow do Studio definido pelo usuário; cena 2 = exemplo dele).
set -eu
cd "${0:A:h:h}"
EP=ep03-a-criacao-do-mundo
NARR=RGymW84CSmfVugnA5tvA
DEUS=7i7dgyCkKt4c16dLtwT3
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar como Deus fez o mundo. Tudo o que existe! Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[whispering] No começo, não havia nada. Tudo era escuro e quieto. [thoughtful] Mas Deus já estava lá. E então, Deus falou."
py tts --force --voice-id $DEUS --out $EP/audio/c3_0.mp3 --text "[calm] Haja luz!"
py tts --force --voice-id $NARR --out $EP/audio/c3_1.mp3 --text "[awe] E a luz apareceu! Que linda. [warm] Deus chamou a luz de dia, e a escuridão de noite. E Deus viu que a luz era boa. Esse foi o primeiro dia."
py tts --force --voice-id $DEUS --out $EP/audio/c4_0.mp3 --text "[calm] Haja um céu bem grande!"
py tts --force --voice-id $NARR --out $EP/audio/c4_1.mp3 --text "[calm] E Deus fez o céu. As nuvens, lá em cima. A água, aqui embaixo. Esse foi o segundo dia."
py tts --force --voice-id $DEUS --out $EP/audio/c5_0.mp3 --text "[calm] Apareça a terra seca!"
py tts --force --voice-id $NARR --out $EP/audio/c5_1.mp3 --text "[happy] Splash! As águas se juntaram, e a terra apareceu. [warm] Deus mandou brotar as plantas: flores, árvores e frutos. E viu que era bom. Esse foi o terceiro dia."
py tts --force --voice-id $DEUS --out $EP/audio/c6_0.mp3 --text "[calm] Hajam luzes no céu!"
py tts --force --voice-id $NARR --out $EP/audio/c6_1.mp3 --text "[gentle] Deus fez o sol, para brilhar de dia. E a lua e as estrelas, para a noite. [whispering] Olha quantas estrelas... [warm] Esse foi o quarto dia."
py tts --force --voice-id $DEUS --out $EP/audio/c7_0.mp3 --text "[calm] Águas, encham-se de peixes! E as aves voem pelo céu!"
py tts --force --voice-id $NARR --out $EP/audio/c7_1.mp3 --text "[playful] Olha os peixes coloridos! E a baleia, enorme! [curious] E os passarinhos? [happy] Piu piu! Deus abençoou todos eles. Esse foi o quinto dia."
py tts --force --voice-id $NARR --out $EP/audio/c8_0.mp3 --text "[happy] Depois, Deus encheu a terra de animais. O leão... auuu! O coelho, pula-pula. A vaca... muuu! [warm] E então, Deus fez o mais especial de todos:"
py tts --force --voice-id $DEUS --out $EP/audio/c8_1.mp3 --text "[warm] Vamos fazer o ser humano, à nossa imagem!"
py tts --force --voice-id $NARR --out $EP/audio/c8_2.mp3 --text "[warm] Deus fez o Adão e a Eva. [awe] E olhou para tudo o que tinha feito... e era muito bom! Esse foi o sexto dia."
py tts --force --voice-id $NARR --out $EP/audio/c9_0.mp3 --text "[softly] No sétimo dia, com tudo pronto, Deus descansou. E abençoou esse dia. [warm] Deus fez o sol, o mar, os animais... e fez você. Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."
echo "AUDIO_V3_DONE"
