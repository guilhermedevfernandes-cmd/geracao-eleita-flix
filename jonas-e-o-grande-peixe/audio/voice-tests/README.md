# Audição obrigatória de vozes — Jonas e o Grande Peixe

Escute cada arquivo com fones. Aprove somente pronúncia e sotaque naturais do português brasileiro.
Se soar português de Portugal, robótico ou inconsistente, troque o voice_id e gere novamente.

- [ ] **Narrador** (`narrator`) — `narrator.mp3` — voice_id `d8ba9f14-8a24-44db-932b-99e16c45bd32` — amostra `a57016779809d06abd88dffe0960b4accd9710965f2a2b4ba2d34eacf41c258f`
- [ ] **Jonas** (`jonas`) — `jonas.mp3` — voice_id `73a45c18-0c56-4642-a61e-f6b303f8ded1` — amostra `85503fc549da30be280abba757e9d762b1f86e2357e2e9cdc1992c3e3499a503`
- [ ] **Voz de Deus** (`deus`) — `deus.mp3` — voice_id `1ad38ba4-9cc4-4f2f-9fde-b0fefdf67ae5` — amostra `0f090a48dc952d2ce08cd966f76e44ac513888c1e60ce2b4098348032890d61b`
- [ ] **Capitão do Navio** (`capitao`) — `capitao.mp3` — voice_id `573e5163-59b3-4926-aab1-951ef2985f81` — amostra `6087dcbdf339a35e986020e0d6a08f98c38540e25ff3e9cd955a5cb129f1b0ff`
- [ ] **Rei de Nínive** (`rei_ninive`) — `rei_ninive.mp3` — voice_id `dc382508-c8bd-443c-8cb2-46e57b8d2e6f` — amostra `48987a846921185e71512ae83846ca70ec14ed6ead1a880ad609e18d357f544a`

Depois de ouvir:

1. Troque qualquer voz inadequada em `characters.tsv` e gere novamente.
2. Para cada amostra aprovada, rode `./approve-voice.sh <key>`.
3. A aprovação fica vinculada ao voice_id, texto de teste e hash do áudio ouvido.
4. Se qualquer um deles mudar, `./gen-narr.sh` bloqueará automaticamente.
