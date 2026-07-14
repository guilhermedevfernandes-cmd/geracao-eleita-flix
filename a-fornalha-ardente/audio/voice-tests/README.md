# Audição obrigatória de vozes — A Fornalha Ardente

Escute cada arquivo com fones. Aprove somente pronúncia e sotaque naturais do português brasileiro.
Se soar português de Portugal, robótico ou inconsistente, troque o voice_id e gere novamente.

- [ ] **Narrador** (`narrator`) — `narrator.mp3` — voice_id `gkqqIm2zTUUewCkNIkTF` — amostra `284ed4d06ceb05fbc740435102f8d683b423b684aaafc89d7eb6b6e2b7ef466d`
- [ ] **Rei Nabucodonosor** (`rei`) — `rei.mp3` — voice_id `r8pRY97Q57nCIMtpOyWA` — amostra `24d4e82d6f9c2ea4d0c95a64b8be9bb7c37fe2ac69a0044c36cc0ec07018d7db`
- [ ] **Sadraque** (`sadraque`) — `sadraque.mp3` — voice_id `NHphTvFqgs01MNV8q4Gn` — amostra `84843a1a6a7350dd66b020b16b4dc3311a5467a2103e1349bca568732c0e10c8`
- [ ] **Mesaque** (`mesaque`) — `mesaque.mp3` — voice_id `5ALQoVCeBkwZZplFpKkO` — amostra `fa1ece751ee4e2a15e1fd764f1fb7267785073436e4b61a1a020427a5d4c7d3f`
- [ ] **Abednego** (`abednego`) — `abednego.mp3` — voice_id `S6JRAR6bdDn0imFzAhjA` — amostra `eb37e9d0d0600035b8d5018001c87ac0dc33cad09ca8b21e95d33920e3c2fb1a`
- [ ] **Capitão da Guarda** (`guarda`) — `guarda.mp3` — voice_id `JtRtm0OrgcgUP6oMWQgc` — amostra `2f39802bea9ef5edffe3eb432bacdbfb97eb7e03701cdc15c73645f339de6ef7`

Depois de ouvir:

1. Troque qualquer voz inadequada em `characters.tsv` e gere novamente.
2. Para cada amostra aprovada, rode `./approve-voice.sh <key>`.
3. A aprovação fica vinculada ao voice_id, texto de teste e hash do áudio ouvido.
4. Se qualquer um deles mudar, `./gen-narr.sh` bloqueará automaticamente.
