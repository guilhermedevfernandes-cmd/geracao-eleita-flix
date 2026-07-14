# Audição obrigatória de vozes — A Fornalha Ardente

Escute cada arquivo com fones. Aprove somente pronúncia e sotaque naturais do português brasileiro.
Se soar português de Portugal, robótico ou inconsistente, troque o voice_id e gere novamente.

- [ ] **Narrador** (`narrator`) — `narrator.mp3` — voice_id `gkqqIm2zTUUewCkNIkTF` — amostra `0a3bbb096b588fdc94bd8faa9817ad5ab215c6c43bb48290b00042df43ea00b8`
- [ ] **Rei Nabucodonosor** (`rei`) — `rei.mp3` — voice_id `r8pRY97Q57nCIMtpOyWA` — amostra `3aa9d3212fc9357b048bdf311a1110b1a5eb2ed23b8c2fc7721a55651224ec72`
- [ ] **Sadraque** (`sadraque`) — `sadraque.mp3` — voice_id `NHphTvFqgs01MNV8q4Gn` — amostra `41d94e961689dd234e198a9dbc90d439d346e68594c0728cc2aa536c2694444f`
- [ ] **Mesaque** (`mesaque`) — `mesaque.mp3` — voice_id `5ALQoVCeBkwZZplFpKkO` — amostra `3ef721bed7f5e5cfdef445cbb47a70e8a279dbe6b01dfd3f61cb92bd531e1d02`
- [ ] **Abednego** (`abednego`) — `abednego.mp3` — voice_id `S6JRAR6bdDn0imFzAhjA` — amostra `14b62f16fc47a8d09146520f3862bd3f49a3de7f9c80dbd2e22cb80d0c2ac8e0`
- [ ] **Capitão da Guarda** (`guarda`) — `guarda.mp3` — voice_id `JtRtm0OrgcgUP6oMWQgc` — amostra `150ecfc5aacbe0942df90aeda963aca227b32341174efdcbb5b237902ea53d73`

Depois de ouvir:

1. Troque qualquer voz inadequada em `characters.tsv` e gere novamente.
2. Para cada amostra aprovada, rode `./approve-voice.sh <key>`.
3. A aprovação fica vinculada ao voice_id, texto de teste e hash do áudio ouvido.
4. Se qualquer um deles mudar, `./gen-narr.sh` bloqueará automaticamente.
