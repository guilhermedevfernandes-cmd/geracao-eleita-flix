#!/bin/zsh
# EP07 O Bebê Moisés — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep07-o-bebe-moises
NARR=RGymW84CSmfVugnA5tvA
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar a história de um bebezinho muito especial: o bebê Moisés. Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[calm] Naquele tempo, o povo de Deus morava no Egito. E o rei de lá não gostava do povo de Deus. Os bebezinhos estavam em perigo. [warm] Foi quando nasceu um bebê muito lindo. [softly] A mamãe dele o escondeu por três meses, com muito amor."
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[gentle] Quando não dava mais para esconder, a mamãe teve uma ideia. [calm] Ela fez um cestinho e passou uma tinta especial, para não entrar água. [softly] Colocou o bebê dentro, bem quentinho... e deixou o cestinho na beira do rio, no meio das plantas."
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[calm] A irmã do bebê, Miriã, ficou de longe, espiando. [gentle] Ela queria ver o que ia acontecer com o irmãozinho."
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[calm] Foi quando a filha do rei do Egito, a princesa, desceu para tomar banho no rio. [curious] Ela viu o cestinho no meio das plantas... [awe] Abriu... e era um bebê! O bebê chorou, e a princesa ficou com muita dó. [warm] Que bebezinho lindo, ela pensou, com o coração cheio de carinho."
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[happy] Aí, Miriã saiu correndo do esconderijo e perguntou: quer que eu chame uma moça para cuidar do bebê para a senhora? [calm] A princesa disse que sim. [warm] E sabe quem a Miriã chamou? A própria mamãe do bebê! [happy] E a princesa ainda pagou a mamãe para cuidar dele. Olha como Deus cuidou de tudo!"
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[calm] O bebê cresceu. E ele foi morar no palácio, como filho da princesa. [awe] Ela deu a ele o nome de Moisés, que quer dizer: tirado das águas. [warm] E Deus tinha planos lindos para a vida dele."
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: Deus cuida dos pequenininhos.

[calm] Dois: Deus usa a família para proteger a gente.

[warm] Três: Deus tem um plano lindo para cada um. Para o Moisés... e para você.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."

py sfx --force --out $EP/sfx/aguinha.mp3 --duration 5 --prompt "gentle little river stream flowing softly, calm water trickle for a preschool cartoon, soothing, no voices"
py sfx --force --out $EP/sfx/surpresa-fofa.mp3 --duration 2 --prompt "cute musical discovery sparkle, soft gasp-like chime flourish of wonder for a preschool show, gentle and sweet, no voices"
echo "AUDIO_EP07_DONE"
