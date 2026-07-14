#!/bin/zsh
# EP08 Davi e Golias — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep08-davi-e-golias
NARR=RGymW84CSmfVugnA5tvA
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar a história de um menino pastor chamado Davi. Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[warm] Davi era o irmão mais novo, e cuidava das ovelhinhas do papai dele. [calm] Ele cuidava com muito amor. [awe] E quando vinha um leão ou um urso pegar uma ovelhinha, Deus ajudava Davi a proteger o rebanho. Deus estava com ele!"
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[calm] Um dia, o papai de Davi pediu: leve estes pães e estes queijos para os seus irmãos, que estão no acampamento do exército. [happy] E Davi foi, bem cedinho."
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[calm] No acampamento, todo mundo estava com medo. [awe] Do outro lado, havia um soldado gigante, muito grandão, chamado Golias. [gentle] Todos os dias ele gritava, zombando do povo de Deus: quem vem lutar comigo? [softly] E ninguém tinha coragem de ir."
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[calm] Davi ouviu aquilo e disse: eu vou lutar com ele! [warm] Deus me ajudou com o leão e com o urso. Deus vai me ajudar agora também. [happy] O rei quis vestir Davi com a armadura dele... mas ficou grandona demais! [gentle] Davi tirou tudo e disse: assim eu não consigo nem andar."
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[calm] Davi foi até o riacho e escolheu cinco pedrinhas bem lisinhas. [softly] Guardou na bolsinha, pegou a funda... e foi."
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[calm] Golias riu de Davi, porque ele era só um menino. [awe] Mas Davi disse: você vem com espada e lança. Eu venho no nome do Senhor! A batalha é do Senhor! [calm] Davi girou a funda... a pedrinha voou... e acertou bem na testa do gigante. [softly] Golias caiu no chão. E acabou! [happy] Deus deu a vitória, e todo mundo comemorou!"
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: a vitória vem de Deus.

[calm] Dois: Deus usa até os pequenininhos.

[warm] Três: quem anda com Deus não precisa ter medo.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."
echo "AUDIO_EP08_DONE"
