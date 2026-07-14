# Audição obrigatória de vozes — A Criação do Mundo

Escute cada arquivo com fones. Aprove somente pronúncia e sotaque naturais do português brasileiro.
Se soar português de Portugal, robótico ou inconsistente, troque o voice_id e gere novamente.

- [ ] **Narrador** (`narrator`) — `narrator.mp3` — voice_id `gkqqIm2zTUUewCkNIkTF` — amostra `0a3bbb096b588fdc94bd8faa9817ad5ab215c6c43bb48290b00042df43ea00b8`
- [ ] **Voz de Deus** (`deus`) — `deus.mp3` — voice_id `r8pRY97Q57nCIMtpOyWA` — amostra `3aa9d3212fc9357b048bdf311a1110b1a5eb2ed23b8c2fc7721a55651224ec72`
- [ ] **Adão** (`adam`) — `adam.mp3` — voice_id `NHphTvFqgs01MNV8q4Gn` — amostra `41d94e961689dd234e198a9dbc90d439d346e68594c0728cc2aa536c2694444f`
- [ ] **Eva** (`eva`) — `eva.mp3` — voice_id `CQvWt7QRuInVGJUccjBp` — amostra `030f31ea0ce595d6ac5ba48d58d275cb922ed3bca38d69df884781c853665524`

Depois de ouvir:

1. Troque qualquer voz inadequada em `characters.tsv` e gere novamente.
2. Para cada amostra aprovada, rode `./approve-voice.sh <key>`.
3. A aprovação fica vinculada ao voice_id, texto de teste e hash do áudio ouvido.
4. Se qualquer um deles mudar, `./gen-narr.sh` bloqueará automaticamente.
