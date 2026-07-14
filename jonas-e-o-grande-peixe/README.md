# Episódio Geração Eleita Flix — pipeline v2

Leia `PRODUCTION-BRIEF.md` antes de preencher os TSVs.

## Arquivos-fonte

`characters.tsv`:

- `key`: identificador usado por cenas e arquivos.
- `name`: nome legível.
- `voice_id`: UUID candidato do Higgsfield ou `-` para personagem sem fala.
- `locale`: `pt-BR` para toda voz falada.
- `voice_approved`: começa como `no`; muda para `yes` somente após audição humana.
- `sheet_prompt`: descrição visual completa em inglês, ou `-` para narrador/voz de Deus.

`scenes.tsv`:

- `id`: sequência `01`, `02`, `03`...
- `act`: função narrativa do beat.
- `shot`: tipo de plano e intenção de lente/câmera.
- `refs`: chaves visuais separadas por vírgula ou `-`.
- `voice`: uma chave do elenco ou `-` para beat sem fala.
- `text`: fala/narração em PT-BR ou `-`.
- `hold`: respiro em segundos depois da fala; em beat silencioso, duração total.
- `image_prompt`: composição do keyframe.
- `motion_prompt`: ação do personagem, ambiente e câmera ao longo do plano.
- `vfx`: efeito visual dedicado ou `-`.
- `sfx`: ambiência/efeitos sonoros ou `-` para silêncio intencional.
- `transition`: `cut`, `match-cut`, `smash-cut`, `whip-pan`, `dip-to-black`, `light-flash` ou `water-wipe`. Match/smash/whip/water são preparados no movimento e finalizados em corte; dip e flash também recebem tratamento na montagem.

Não use TAB dentro de um campo: TAB é o separador do arquivo.

## Ordem de produção

```bash
./validate.sh script
./make-roteiro.sh
./approve-script.sh  # somente depois da aprovação editorial
./gen-voice-tests.sh
# ouvir e executar ./approve-voice.sh <key> para cada voz
./gen-narr.sh       # fixa a duração real antes de aprovar os clipes
./gen-sheets.sh
# revisar identidade/figurino e executar ./approve-visual.sh reference all
./gen-frames.sh
# revisar composição/continuidade e executar ./approve-visual.sh frame all
./make-kit.sh
./gen-clips.sh       # ou animação manual guiada pelo KIT
./register-clips.sh  # obrigatório para clipes baixados manualmente
# revisar física/câmera/morphing e executar ./approve-visual.sh clip all
./gen-sfx.sh
./gen-score.sh       # opcional; também aceita audio/bgm.mp3 externo
./approve-music.sh   # obrigatório se audio/bgm.mp3 existir
./validate.sh assembly
./assemble.sh
```

Use `--dry-run` em `gen-narr.sh`, `gen-sfx.sh` e `gen-score.sh` para validar comandos sem consumir créditos.

`all` é uma confirmação humana em lote: use somente depois de abrir e revisar todos
os arquivos daquela etapa. A aprovação guarda o hash exato; qualquer regeneração
obriga uma nova revisão.

Se o validador marcar alguma fala como linguisticamente ambígua, revise essas linhas
uma a uma e use `./approve-script.sh --confirm-ambiguous-pt-br`. Sem essa confirmação
explícita, o roteiro não avança.
