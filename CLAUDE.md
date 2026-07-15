# Geração Eleita Flix — Playbook de Produção

> **Fonte canônica de conhecimento do canal.** Leia este arquivo INTEIRO antes de produzir
> qualquer episódio. Ele existe para que qualquer Claude Code, em qualquer máquina
> (Mac do Guilherme ou Windows da esposa), produza no MESMO padrão aprovado.
> Sempre que uma lição nova for aprendida em produção, ATUALIZE este arquivo e faça commit.

## 1. O que é o canal

Canal de episódios bíblicos infantis, em português do Brasil, com duas linhas:

| Linha | Público | Estilo visual | Pastas |
|---|---|---|---|
| **Baby (linha principal)** | 2-3 anos | Chibi estilo Cocomelon (ver DNA de estilo) | `ep01-*` a `ep12-*` (numeradas) |
| **Madura (pausada)** | 5-11 anos | Pixar-like | `a-criacao-do-mundo`, `a-fornalha-ardente`, `jonas-e-o-grande-peixe` (finalizadas); demais sem master final |

**Regra nº 1 — inegociável:** fidelidade bíblica. Antes de escrever/gravar/gerar QUALQUER
coisa, rode o checklist de [`FIDELIDADE-BIBLICA.md`](FIDELIDADE-BIBLICA.md). Resumo: o tom
é amigável, os FATOS são os da Bíblia. Nunca inventar motivos, eventos, gestos ou falas;
toda cena com referência bíblica anotada (livro + capítulo:versículo); a lição final dá a
glória a Deus; o enganador nunca fica simpático na narração.

**Regra nº 2:** o humano é o revisor. TODO asset gerado (imagem, vídeo, áudio) passa por
revisão visual/auditiva antes de aprovar. Nunca montar episódio com asset não revisado.

## 2. Ferramentas e ambiente

- **Imagens:** `nano-banana-pro` — via OpenArt MCP (i2i com `visualReferences` dos
  personagens-mestre) ou HiggsField MCP (`nano_banana_pro`, param `medias` com job IDs).
  Resolução 2k, aspecto 16:9.
- **Vídeos:** OpenArt MCP `pixverseV6` (image2video, 720p, 5s, `generateAudio: false`,
  `startFrame` aceita URL direto). Peças premium (intro, aberturas): Kling 3 Omni ou
  Seedance 2.0 (`endFrame=startFrame` trava enquadramento).
- **Áudio (narração, SFX, BGM): SEMPRE ElevenLabs via API direta** — NUNCA o TTS do
  HiggsField (seed_audio/text2speech_v2 rejeitados: "parece caipira"). Script pronto:
  [`scripts/elevenlabs_audio.py`](scripts/elevenlabs_audio.py) (comandos `discover`/`narrate`/`sfx`/`music`).
  Chave: variável `ELEVENLABS_API_KEY` ou arquivo `~/.config/gerecao-eleita-flix/elevenlabs.env`
  (o script lê os dois; NUNCA commitar a chave).
- **Montagem:** Python + ffmpeg local (leve; qualquer notebook dá conta).
- **Conectores MCP necessários na conta claude.ai:** OpenArt e Higgsfield.

## 3. Pipeline de um episódio novo (linha baby)

1. **Roteiro** — `ROTEIRO-EPxx.md` na pasta `epxx-slug/`. Cenas com base bíblica anotada,
   texto de narração no tom da seção 6, mínimo de planos da etapa 3. Rodar checklist de
   fidelidade ANTES de seguir.
2. **Imagens-mestre** — personagens novos do episódio viram masters (gerar, revisar,
   registrar ID na seção 5 deste arquivo + `refs-openart.json`). Personagens recorrentes:
   usar os IDs existentes como referência em TODA cena.
3. **Imagens de cena** — **mínimo 20 planos por episódio** (cada cena rende 2-3 planos:
   aberto / close / detalhe da ação) para o vídeo não ficar repetitivo. Sempre com os
   masters como referência + DNA de estilo no fim do prompt.
4. **GATE de revisão de imagem** (checklist na seção 10) — só avança o que passou.
5. **Vídeos** — PixVerse V6 i2v 5s por plano aprovado. Máx **8 gerações simultâneas**
   no OpenArt (`PARALLEL_LIMIT_EXCEEDED`) — submeter em ondas. Prompt de movimento
   defensivo: `STATIC camera, stays in place, no new characters`.
6. **GATE de revisão de vídeo** (seção 10).
7. **Áudio** — narração + SFX + BGM no ElevenLabs (seção 6 e 7). Registrar tudo em
   `audio/` da pasta do episódio.
8. **Montagem** — script `montar_epxx.py` copiado do de referência
   [`ep03-a-criacao-do-mundo/montar_ep03.py`](ep03-a-criacao-do-mundo/montar_ep03.py). Regras técnicas na seção 8.
9. **QA no arquivo final** (seção 9).
10. **Versão COM-INTRO (obrigatória)** — o episódio NÃO está terminado sem
    `EPxx-COM-INTRO-*.mp4` (seção 8.3).
11. **Capas** — 16:9 e 9:16 (`capa-epxx-16x9.png` / `capa-epxx-9x16.png`). Revisar TEXTO
    do título (nano-banana às vezes duplica palavra — pedir título "EXACTLY ONCE").
    **Tipografia oficial do canal (padrão `ep12-*/capa-ep12-9x16.png`):** letras 3D
    "infladas"/brilhantes (glossy bubble), arredondadas, com contorno creme/branco GROSSO
    e sombra suave. Cor em DUAS camadas quentes: **1ª linha AMARELO, 2ª linha LARANJA**
    (ex.: "DANIEL" amarelo / "E OS LEÕES" laranja; "Moisés" amarelo / "e o Mar Vermelho"
    laranja). Na 9:16 o título fica empilhado em 2 linhas no topo. NUNCA cada letra de uma
    cor diferente (o usuário chama de "carnaval de cores" e reprova). No prompt:
    `big glossy inflated 3D bubble letters, first line bright YELLOW, second line warm ORANGE,
    thick creamy white outline + soft drop shadow, only these two warm colors, NOT rainbow`.
12. **Registrar aprendizados** — lições novas → atualizar este CLAUDE.md + commit.

**Arquivos padrão da pasta de episódio:** `ROTEIRO-EPxx.md`, `imagens-resources.tsv`
(plano→resourceId→URL), `videos-jobs.tsv`, `imagens/`, `videos/`, `audio/`, `sfx/`,
`montar_epxx.py`, `EPxx-PREVIEW-*.mp4`, `EPxx-COM-INTRO-*.mp4`, capas.
(Mídia não vai para o git — os TSVs são o mapa para rebaixar tudo da nuvem.)

## 4. DNA de estilo (colar no FIM de todo prompt de imagem)

```
Soft Cocomelon-style chibi proportions for a preschool cartoon aimed at toddlers aged 2-3:
oversized round heads, huge sparkling eyes with big star highlights, tiny button noses,
rosy blush cheeks, chubby short bodies, plush clay-like soft 3D render with matte velvety
textures, bright cheerful candy colors, ultra cute, kawaii, huggable plush-toy look,
wholesome G-rated preschool animation still, everything rounded with no sharp edges,
high quality render
```

Com referências, acrescentar: `Keep the EXACT same character designs, colors and
proportions as the reference images.`

Rostos kawaii em sol/lua/nuvens/flores/árvores = estilo aprovado do canal.
Em luz divina/objetos = NÃO. Presença de Deus = luz/brilho SEM rosto
(`pure formless light, no face, not a character`).

## 5. Personagens-mestre (IDs para referência visual)

### HiggsField (job IDs — param `medias`)

| Personagem | Job ID |
|---|---|
| Vovô Noé | `88646dbb-8103-43b0-a0cb-67a43d8c908d` |
| Noé v1 (alternativo) | `88619132-241b-4809-a188-70d0022476f8` |
| Juba (leãozinho, mascote — cameo VISUAL em todo episódio) | `335147b1-7167-485b-83e0-626e67c80f72` |
| Nina (pombinha, cameo) | `05291622-b344-437e-99fa-5e75289b0840` |
| Adão (EP02) | `813444c3-aaff-495f-8713-57e0321b9e19` |
| Eva (EP02) | `1ca5f63c-6640-4341-9492-ce18072860ff` |
| Cobrinha (serpente Gn 3 — design fofo, narração SEMPRE a marca como enganadora; NUNCA nome carinhoso) | `a89715d5-4323-4816-88b2-bb25a6e657eb` |
| Daniel | `ab7dbe80-10ff-41c3-9fb6-d7b16d03db1c` |
| Davi | `f26a2066-01c3-472e-8ef0-0e0dfe0eca66` |
| Golias | `8649ce47-c9c5-4540-9ac1-49cb830be5db` |
| João Batista | `afddcdbe-48cc-4ae5-a525-c1a7ccdc7fbb` |
| Jesus | `f0eb5488-f096-4dcb-a38d-bfafbb8aa90f` |

### OpenArt (resource IDs — `visualReferences`; uploads mapeados em `refs-openart.json`)

| Personagem | Resource ID |
|---|---|
| Bebê Moisés (EP07) | `TBz2yp9uFUz5WKyHpuEH` |
| Miriã (EP07) | `ZYgcxwGrY22myna2Db2B` |
| Mamãe Joquebede (EP07) | `89yJfYDiuL8lz5sRPMXH` |
| Princesa do Egito (EP07) | `U36zFWT3Hmn7SGO5y9FX` |
| João Batista (EP10) | `3pQO80vge6x1s53bA9sn` |
| Jesus chibi adulto (EP10+ — reusar em eps da vida de Jesus) | `24Dv0IiQYAKMfPXuqDmH` |
| Enganador/serpente escura (EP11) | `JsLQYmX51sUVYyJc2t4h` |
| Anjo (EP09) | `PoqqLpbbAmVyNehq7sN4` |
| Moisés adulto (EP12) | `WN8Xju422Lj0amJD8U5J` |
| Faraó (EP12) | `EeT86wkJEie7gmhJ6r8s` |
| José v1 | `RqrW6KgZ7njyIQNRoRE8` |
| José v2 (casaco aberto listras VERTICAIS + calça — versão oficial) | `uMnj6n19iKNSyGM4ktRT` |
| Jacó | `geEH33YLWP5k6pf9C3JJ` |
| Jonas | `8g7hzg6q9JCBUQh3Veig` |
| Baleia | `jMzYCLoFE6DEpICQ76XC` |
| Davi | `4wiieQxEuYk2xkcqtuNH` |
| Golias | `qPZZZLHFBqVnRbWxNS1Q` |
| Daniel idoso ~80 anos (EP13 — cova dos leões acontece sob Dario, Dn 6; NÃO usar o Daniel jovem) | `hDupNNk3Vti7dhDcbYW4` |
| Rei Dario (EP13) | `RyoU9ycCjj8Cz2jRS1vl` |
| Oficiais invejosos ×2 (EP13 — vilão-cômico) | `i6WyMlnAW2x4VTxG7nTW` |
| Daniel idoso ~80 **linha madura/Pixar** (`daniel-na-cova-dos-leoes`, Dn 6 sob Dario) | `zVgV8cYjisqLkd7D366Q` |
| Adão **madura/Pixar** (`adao-e-eva`) | `EgS1Vc4m51NDd63hSd3c` |
| Eva **madura/Pixar** (`adao-e-eva`) | `4vQoW2rKUcT3abqr49hq` |
| Serpente enganadora **madura/Pixar** (`adao-e-eva`) | `02EaWaVWCuj1JAbygiLa` |

Linha madura (HiggsField): Adão v1 `9e913a82-236b-407a-bbf0-bde10babcdc1` ·
Eva v1 `012b847f-1044-4cf9-b290-8f01fc6e2182` · Jonas `9607b390-b035-4ff6-be86-2c8a616a3ba9` ·
trio da fornalha nos `assets/*.higgsfield.json`.

## 6. Áudio — ElevenLabs (padrão oficial)

**Vozes (a partir do EP03):** narradora `RGymW84CSmfVugnA5tvA` · Deus `7i7dgyCkKt4c16dLtwT3`.
(Elenco antigo "GE Flix" nos EP01-02: Eva `CQvWt7QRuInVGJUccjBp`, Voz de Deus `r8pRY97Q57nCIMtpOyWA`.)

**Narração — workflow Eleven v3:**
- `POST /v1/text-to-speech/{voice_id}` com `model_id: eleven_v3` +
  `voice_settings {stability: 1.0}` ("Robusto"; v3 só aceita 0.0/0.5/1.0).
- **SEM outros voice_settings customizados** (deixavam a fala acelerada/forçada).
- **Audio tags** de expressão em inglês, moderadas, dentro do texto: `[warm]`, `[happy]`,
  `[calm]`, `[awe]`, `[whispering]`, `[playful]`, `[curious]`, `[softly]`. Falas de Deus = `[calm]`.
  NUNCA usar tags com modelos v2 (eles LEEM as tags em voz alta).
- **Blocos que precisam de consistência = UM request único** (ex.: reflexão final com as
  3 lições), com quebras duplas de linha para as pausas. Segmentos muito curtos gerados
  separadamente variam a pronúncia pt-BR (a narradora já "virou carioca" numa reflexão).
  `previous_text`/`next_text` NÃO funcionam no v3 (HTTP 400).
- **A PRIMEIRA palavra do request é a mais propensa a distorção** — nome próprio como 1ª
  palavra já virou outra coisa ("José" → "Rosé"). Proteger com artigo ("O José tinha...").
  O STT scribe NÃO detecta esse erro (corrige pelo contexto) — conferir DE OUVIDO.
- Nunca regravar segmento já aprovado sem necessidade (cada geração é loteria de prosódia).

**Eleven v3 na linha madura (pipeline zsh de `a-fornalha-ardente` — migrado em 2026-07-14):**
- O modelo vem de `TTS_JOB_TYPE` em `_pipeline/audio_contract.py` (geração e validação em
  lockstep); `elevenlabs_audio.py` manda `voice_settings {stability: 1.0}` quando o modelo
  é v3. Tags de expressão vão NO texto de `scenes.tsv` (ex.: `[warm] Na grande Babilônia...`);
  `episode_pipeline.py` as ignora na contagem de palavras e na detecção de idioma (`spoken_text`).
- **v3 fala mais rápido que o v2**: ritmo real medido ≈ **161 wpm** (v2 ≈ 138). Ao migrar um
  episódio, a duração real cai ~10%; compensar aumentando os `hold` (respiro que também deixa
  o BGM aparecer) e alinhar `WORDS_PER_MINUTE` (meta.env + POLICY_INTEGERS do pipeline local).
- Trocar narração invalida em cascata: voice-tests (re-ouvir + re-aprovar), roteiro
  (make-roteiro + approve-script), SFX (duração por cena no fingerprint) e BGM (duração total
  no fingerprint) — regenerar tudo ANTES do assemble.
- Ducking do BGM no `assemble.sh`: `sidechaincompress threshold=0.05:ratio=3:attack=25:release=700`.
  O antigo `ratio=10:threshold=0.025` esmagava a música até ficar inaudível sob narração contínua.

**Redo do `daniel-na-cova-dos-leoes` (madura, scripts SIMPLES do topo — 15/07/2026):** este
episódio usa os scripts `gen-*.sh`/`assemble.sh` da própria pasta (NÃO o `_pipeline` da
fornalha). Lições do redo "Daniel idoso":
- **Fidelidade:** a cova dos leões é Dn 6, sob Dario — Daniel é IDOSO (~80), não jovem.
  Master madura OpenArt `zVgV8cYjisqLkd7D366Q`; corrigido também o texto ("um jovem" → "um homem"
  na cena 04). Personagens que aparecem em cenas MANTIDAS (Rei, oficiais, anjo) NÃO podem mudar
  de visual → subir os `assets/*_ref.png` EXISTENTES como `visualReferences` (não regerar).
- **Áudio = ElevenLabs v3 DIRETO:** `gen-narr.sh` foi reescrito p/ chamar
  `../scripts/elevenlabs_audio.py tts` (nunca mais o `text2speech_v2` do HiggsField). Vozes robustas
  + solenes: narrador **Lucas – Deep & Profound** `GIuLCSVfgJaUuh7hYOY8`, Daniel idoso **Felipette**
  `JtRtm0OrgcgUP6oMWQgc`, Rei Dario **Adam Borges** `ZqE9vIHPcrC35dZv0Svu`. Tags de emoção `[warm]`/`[calm]`/
  `[awe]`/`[sad]`... no início da fala em `scenes.tsv` (v3 interpreta; conferido por STT scribe que NÃO
  são lidas em voz alta).
- **Vídeo via OpenART** (HiggsField estava sem créditos — só 70): frames por `nano-banana-pro`
  image2image 16:9/2K com os refs; clipes por `kling-3-omni` image2video **std + generateSound=false**
  (125 créditos/clipe; a montagem escala p/ 1080 e tira o áudio). **Cap de 8 gerações Kling simultâneas**
  (`PARALLEL_LIMIT_EXCEEDED`) → ondas de 8.
- **SFX + BGM:** `mix_sfx.py` (novo) mistura narração (dominante) + BGM suave em loop + SFX de
  momentos-chave posicionados por cena (`assemble.sh` grava `build/offsets.txt`); `alimiter=limit=0.60:level=0`
  (o 0.63 deixou o pico em -3.8dB > -4dB). BGMVOL baixado p/ 0.10.

**SFX:** `POST /v1/sound-generation`. **Novos a cada episódio** (reaproveitar só 1-2
genéricos, ex.: passarinho — "precisamos inovar"). Chuva/ambientes saem MUITO baixos
(~-48dB): aplicar ganho ×4 na mixagem. **NUNCA usar sininhos/twinkle/guizos** (o usuário
chama de "som de chocalho" — removidos do EP05/EP06).

**BGM:** `POST /v1/music` — instrumental infantil **alegre e saltitante** (ukulele,
marimba, palminhas). NUNCA lullaby/caixinha de ninar. A música oficial do canal
(`musica-oficial-geracao-eleita.mp3`) NÃO é trilha de fundo de episódio — só da intro.

## 7. Narração para 2-3 anos (tom) e mixagem

**Tom:** SÓBRIO e caloroso, sem forçar fofura. Diminutivos com MUITA parcimônia (1
"amiguinho" na abertura é ok; NUNCA "historinha/nadinha/quietinho/terrinha/dedinhos").
Onomatopeias só onde naturais e moderadas (auuu, muuu, splash — NUNCA "TCHAAAM/FUUUSH"
em caps). Frases curtas. Pergunta à criança 1-2× por episódio (não a cada 20-30s).
Tensão sempre "aconchegante", nunca escura/assustadora. Bordão que encerra:
**"Deus cuida de mim, Deus cuida de você!"**

**Mixagem (níveis validados — o usuário é MUITO sensível a áudio alto; na dúvida, mais baixo):**

| Elemento | Volume |
|---|---|
| Narração | dominante |
| BGM infantil — abertura | 0.10 |
| BGM infantil — meio | **0.065** (janela só-BGM ≈ -44dB mean, quase subliminar) |
| BGM infantil — outro | 0.08 |
| BGM da reflexão (`assets/bgm-reflexao-oficial.mp3`) | 0.09, entra com crossfade |
| SFX | 0.18–0.35 (chuva ×1.6 do gerado; toc-toc 0.32) |
| **Pico geral do master** | **≤ -4dB** |

## 8. Montagem e regras técnicas ffmpeg

### 8.1 Estrutura e ritmo do episódio

- Intro branca 2s / outro branco 3s; clipes em **0.75x**; pausa de **2.5s entre cenas**
  (só BGM); **0.7s** entre falas de vozes diferentes na mesma cena; pausas interativas ~2.2s.
- Multi-plano: cortes secos dentro da cena, fade branco entre cenas.
- **Reflexão final encerra TODO episódio:** "E o que aprendemos com essa história? Vem
  lembrar comigo." + 3 lições curtas e literais da passagem + bordão + tchau. Gravada em
  request único; trilha própria (`assets/bgm-reflexao-oficial.mp3` — MESMA em todos os
  eps, assinatura do quadro); visual = recap de clipes aprovados do episódio (custo zero).
- Duração alvo: ~2:10–3:00 (EP03–EP12 ficaram entre 2:11 e 2:58).

### 8.2 Regras ffmpeg (aprendidas com erro — NÃO repetir)

- `format=yuv420p` / `-pix_fmt yuv420p` em TODO encode (sem isso o libx264 pode escolher
  yuv444p e o QuickTime mostra só tela branca).
- Concat final SEMPRE re-encodado (concat `-c copy` entre encodes diferentes corrompe).
- `alimiter=limit=0.63:level=0` — o `:level=0` é OBRIGATÓRIO (sem ele o alimiter
  re-normaliza para ~0dB e estoura a regra do pico ≤ -4dB).
- `-movflags +faststart` no master final.
- Overlay de PNG estático com fade exige `-loop 1` na entrada (senão a logo some).
- Shell: cuidado com interpolação de variável junto de `:` em filtros ffmpeg
  (no zsh, `"$n:layout"` vira modificador `:l` — usar `${n}:layout`; no Windows/
  PowerShell, preferir escrever os filtros em arquivo de script Python, não inline).

### 8.3 Versão COM-INTRO (obrigatória em todo episódio)

Concatenar [`intro-oficial/intro-geracao-eleita-flix-6s-1080p.mp4`](intro-oficial/intro-geracao-eleita-flix-6s-1080p.mp4)
antes do preview: intro convertida para fps=30 + mono 44.1kHz
(`pan=mono|c0=0.5*c0+0.5*c1`), `concat=n=2:v=1:a=1`, re-encode crf 18 yuv420p +
aac 192k + faststart. Episódio sem `EPxx-COM-INTRO-*.mp4` = episódio não terminado.

## 9. QA final (no ARQUIVO FINAL, não nos intermediários)

1. `ffprobe`: profile=High, pix_fmt=yuv420p, fps=30.
2. Extrair frames em 3-4 pontos e OLHAR (extrair frame com ffmpeg não prova reprodução —
   ffmpeg decodifica coisas que player não toca; por isso o ffprobe também).
3. `volumedetect`: pico ≤ -4dB.
4. Ouvir a narração inteira (erros de pronúncia que o STT não pega).

## 10. Checklists de revisão de assets

**Imagem (revisar TODA imagem gerada):**
- Estilo fugiu do DNA? Personagem igual ao master?
- **Contar braços/mãos/pernas de cada personagem** (nano-banana já desenhou Jesus com 3 braços).
- Objeto anacrônico inventado? (barcos, casinhas, chapéus em bichos, bicho fora do dia
  da criação) → negativar no prompt: `no boats, no houses, no hats, no animals, no people`.
- TEXTO desenhado na imagem? Nunca usar frase conceitual no prompt ("celebration of
  light" virou texto escrito); sempre `no text, no words`.
- Elemento que só aparece depois na história (arca pronta antes da construção)?
- Rosto kawaii onde não deve (luz divina/objetos)?

**Vídeo (revisar TODO clipe):**
- Personagem duplicado? Saiu do quadro? Grupo caminhou até a câmera destruindo a composição?
- Personagem escondido "levantou" e ganhou roupa inventada? → travar no prompt:
  `stays ducked/hidden the entire time, never rises, clothes stay hidden`.
- Fim do clipe estranho (serpente ganha carinha cômica, gigante caído levanta)? →
  verificar se a janela USADA na montagem está limpa antes de regenerar (trim resolve grátis).
- **CUIDADO com o bumerangue da montagem em cena de "estado final"** (personagem caído,
  porta fechada etc.): quando o clipe é mais curto que o tempo do plano, o script de
  montagem toca o clipe REVERTIDO no fim — um caído "levanta" mesmo com o clipe limpo
  (EP08: Golias). Solução padrão: set `FREEZE` no `montar_epxx.py` — planos listados
  congelam o último frame (`tpad=stop_mode=clone`) em vez de reverter (ver `ep08/montar_ep08.py`).
- Virou anoitecer sem pedir? (PixVerse faz isso.)
- **Montar episódio a partir de clipes prontos com nomes opacos (ex.: `openart-<uuid>_seed..._<ts>_<hash>.mp4`)
  — EP14/Rute:** identifique CADA clipe olhando um frame e amarre `plano→arquivo` por uma CHAVE ESTÁVEL
  (o `<hash>` de 8 chars do fim do nome), NUNCA pela POSIÇÃO numa lista ordenada. Ordenações diferentes do
  mesmo diretório dão ordens diferentes (`ls|sort -t_ -k4` ordena pelo hash; `sort(key=ts)` em Python ordena
  por outro campo) — se você vê os frames numa ordem e gera os symlinks noutra, os planos apontam para os
  clipes ERRADOS e o episódio inteiro embaralha SEM nenhum erro de execução. Blindagem obrigatória: extrair
  **1 frame por cena do MASTER final** e conferir olho a olho que a ordem narrativa bate (ver seção 9.2).
- **Narração mais longa que os clipes (só 5s cada):** na linha baby remontada sobre vídeo pronto, a fala pode
  passar de 3min e os 21×5s não cobrem. Solução no `montar_epxx.py`: ESTICAR cada plano com `setpts` até
  preencher seu tempo (slow-mo suave, ~0.4–0.75x) em vez de reverter (bumerangue treme) ou travar; só congela
  o resto se o stretch passar de ~2.9x (`MAX_STRETCH`, ≈0.34x). Ver `ep14- Rute/montar_ep14.py`.

## 11. Armadilhas de plataforma

- **Google content policy (nano-banana):** descrição tipo "pulling clothing off a boy"
  bloqueia → reescrever o estado, não a ação ("casaco já tirado, irmão segurando").
- **Filtro HiggsField:** cena de batismo/rio pode dar falso positivo "nsfw" → reescrever
  com `fully dressed in robe`, `pouring water from his cupped hand`, `shallow river`,
  `family-friendly children's cartoon`.
- **PixVerse V6 no OpenArt:** aceita `duration` livre 1-15s; máx 8 jobs simultâneos.
- **Kling 3 Omni (OpenArt):** resolution "pro" = 1080p mas entrega 1928x1072 → normalizar
  `scale=1942:1080,crop=1920:1080`; ~7min por job; exige upload próprio + `metadata`
  completo do `openart_upload_metadata_get`.

## 12. Custos de referência (OpenArt)

- PixVerse V6 i2v 720p/5s = 70 créditos (63 com desconto MCP 10%); 1080p = 150.
- Episódio típico (20+ planos) ≈ 1.400–1.600 créditos só de vídeo. Confirmar saldo antes
  de submeter as ondas.

## 13. O que NÃO está no repositório (e onde vive)

- **MP4/PNG/áudio dos episódios**: no computador que produziu + masters nas plataformas
  (OpenArt/HiggsField/ElevenLabs). Os mapas `imagens-resources.tsv` e `videos-jobs.tsv`
  de cada episódio têm os resourceIds/URLs para rebaixar qualquer asset.
- **Zips de entrega por tier**: `zips-tiers/` (local).
- **Chaves de API**: `~/.config/gerecao-eleita-flix/elevenlabs.env` de cada máquina.
- **Este repositório é a fonte de verdade do CONHECIMENTO** (playbook, roteiros, scripts,
  mapas). Produziu algo novo? Commite roteiro + TSVs + lições no mesmo dia.

## 14. Setup numa máquina nova

Ver [`GUIA-INSTALACAO-WINDOWS.md`](GUIA-INSTALACAO-WINDOWS.md) (passo a passo completo para Windows;
no macOS o equivalente é `brew install git python ffmpeg`).
