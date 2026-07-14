#!/bin/zsh
# EP05 Jonas e a Baleia Amiga — Eleven v3 + stability Robusto + audio tags (padrão EP03 v3)
set -eu
cd "${0:A:h:h}"
EP=ep05-jonas-e-a-baleia-amiga
NARR=RGymW84CSmfVugnA5tvA
DEUS=7i7dgyCkKt4c16dLtwT3
py() { python3 scripts/elevenlabs_audio.py "$@"; }

py tts --force --voice-id $NARR --out $EP/audio/c1_0.mp3 --text "[warm] Olá, amiguinho! Que bom te ver. [happy] Hoje eu vou contar a história de Jonas e o peixe mais grandão que você já viu! Vem comigo."
py tts --force --voice-id $NARR --out $EP/audio/c2_0.mp3 --text "[calm] Jonas era um homem que ouvia a voz de Deus. Um dia, Deus falou com ele:"
py tts --force --voice-id $DEUS --out $EP/audio/c2_1.mp3 --text "[calm] Jonas! Vá até a cidade de Nínive. Avise o povo de lá: eles estão fazendo coisas muito erradas."
py tts --force --voice-id $NARR --out $EP/audio/c3_0.mp3 --text "[gentle] Mas Jonas não quis ir. [softly] Ele fugiu! Correu para o porto, entrou num barco... e partiu para bem, bem longe de Nínive."
py tts --force --voice-id $NARR --out $EP/audio/c4_0.mp3 --text "[calm] Mas aí, veio um vento muito forte. [gentle] O mar ficou bravo, cheio de ondas! O barco balançava para lá e para cá. Os marinheiros ficaram com medo. [calm] E Jonas contou: é por minha causa. Eu fugi de Deus. Podem me colocar no mar. [softly] Splash! E o mar... ficou calminho."
py tts --force --voice-id $NARR --out $EP/audio/c5_0.mp3 --text "[awe] E Deus mandou um peixe bem grande, enorme! [playful] Glub! O peixe engoliu Jonas. [calm] E Jonas ficou lá, na barriga do peixe, três dias e três noites."
py tts --force --voice-id $NARR --out $EP/audio/c6_0.mp3 --text "[softly] Lá dentro, no escurinho, Jonas orou. Conversou com Deus. [warm] E agradeceu: Obrigado, Senhor, porque eu estou vivo! A salvação vem do Senhor! [gentle] E Jonas prometeu: Agora eu vou obedecer. [happy] Então o peixe nadou, nadou... e deixou Jonas são e salvo na praia."
py tts --force --voice-id $NARR --out $EP/audio/c7_0.mp3 --text "[calm] E Deus falou com Jonas de novo:"
py tts --force --voice-id $DEUS --out $EP/audio/c7_1.mp3 --text "[calm] Jonas, vá até Nínive. Fale ao povo o que eu te disser."
py tts --force --voice-id $NARR --out $EP/audio/c7_2.mp3 --text "[happy] E dessa vez... Jonas foi! [calm] Ele avisou o povo. E o povo de Nínive ouviu, e parou de fazer o mal. [warm] E Deus perdoou todinhos eles."
py tts --force --voice-id $NARR --out $EP/audio/c10_full.mp3 --text "[warm] E o que aprendemos com essa história? [thoughtful] Vem lembrar comigo.

[calm] Um: quando Deus fala, o melhor é obedecer.

[calm] Dois: Deus ouve a nossa oração em qualquer lugar. Até na barriga de um peixe!

[warm] Três: Deus perdoa quem deixa de fazer o mal.

[warm] Deus cuida de mim, Deus cuida de você! [happy] Tchau! Até a próxima."

py sfx --force --out $EP/sfx/apito-barco.mp3 --duration 2.5 --prompt "cute cartoon boat horn toot, cheerful and soft, toy ship whistle for a preschool show, no voices"
py sfx --force --out $EP/sfx/vento-mar.mp3 --duration 5 --prompt "gentle cartoon sea storm: soft wind whoosh with rounded wave splashes, cozy not scary, for toddlers, no voices, no thunder"
py sfx --force --out $EP/sfx/glub.mp3 --duration 2 --prompt "cute cartoon gulp swallow sound, big soft glub glub with a little water bubble pop, funny and gentle for preschool animation, no voices"
echo "AUDIO_EP05_DONE"
