# Produção — O Nascimento de Jesus (madura/Pixar, série de Jesus)

> Kit criado em 16/07/2026. Pipeline = o mesmo do `jose/` (OpenArt: nano-banana-pro
> 2K i2i + kling-3-omni std sem som · ElevenLabs v3 · assemble.sh local).
> **Teto de créditos OpenArt autorizado: 6.000** (episódios de Jesus = nível elevado).

## Status

| Etapa | Status |
|---|---|
| 1. Roteiro + checklist de fidelidade | ✅ `roteiro.md` (checklist rodado 16/07) |
| 2. scenes.tsv (27 cenas) / characters.tsv (5 masters) / meta.env | ✅ |
| 3. Narração ElevenLabs v3 (27 arquivos em `audio/`) | ✅ gerada — **falta revisão DE OUVIDO** (pt-BR, 1ª palavra, prosódia) |
| 4. SFX (5) + BGM em `sfx/` e `audio/bgm.mp3` | ✅ gerados — falta revisão de ouvido |
| 5. Masters OpenArt (5 refs) | ⏳ pendente — PRECISA do conector OpenArt MCP |
| 6. Frames (27) + GATE de revisão de imagem | ⏳ pendente |
| 7. Clipes Kling (27, ondas de 8) + GATE de vídeo | ⏳ pendente |
| 8. assemble.sh + QA (pico ≤ -4dB, yuv420p) | ⏳ pendente |
| 9. COM-INTRO obrigatória | ⏳ pendente |
| 10. Capas 16:9 + 9:16 (azul-noite + prata, trim dourado, SEM byline) | ⏳ pendente |

**⚠ Bloqueio atual:** a sessão do VSCode não tem o conector OpenArt MCP (nem HiggsField).
A geração visual (etapas 5-7 e 10) deve ser feita numa sessão com o conector OpenArt
da conta claude.ai, seguindo este documento. Alternativa: CLI `higgsfield`/`kie`
via `gen-sheets.sh`/`gen-frames.sh`/`gen-clips.sh` (mas o orçamento aprovado é OpenArt).

## Orçamento (teto 6.000 créditos OpenArt)

| Item | Qtde | Créditos | Total |
|---|---|---|---|
| Masters nano-banana-pro 2K | 5 | 40 | 200 |
| Frames nano-banana-pro 2K i2i | 27 | 40 | 1.080 |
| Clipes kling-3-omni std 5s sem som | 27 | 125 | 3.375 |
| Capas (16:9 + 9:16) | 2 | 40 | 80 |
| **Subtotal** | | | **4.735** |
| Reserva p/ retakes (frames/clipes reprovados no GATE) | | | 1.265 |

Se estourar: regenerar só o FRAME (40) e animar com Ken-Burns local (custo zero),
como nas cenas 24/25 do José.

## Fase OpenArt — passo a passo (sessão com o conector)

1. **Masters (5):** gerar cada `sheet_prompt` de `characters.tsv` com o REFFRAME de
   `gen-sheets.sh` ("ONE single character, solo, full-body, A-pose, plain light-gray
   background") + STYLE do `meta.env`. Salvar em `assets/<key>_ref.png`, subir como
   referência e registrar id/url em `refs-openart-madura.json` + seção 5 do CLAUDE.md.
   **GATE humano** antes de seguir.
2. **Frames (27):** para cada linha de `scenes.tsv`, nano-banana-pro i2i 16:9/2K com
   `visualReferences` = ids dos masters na ordem da coluna `refs` ("reference image 1"
   = primeiro ref). Prompt = `image_prompt` + guarda anticlone + STYLE. Salvar
   `frames/NN.png` e mapear em `frames-openart.tsv` (id → resourceId → arquivo).
   Cena 16 (multidão de anjos) é SEM ref — intencional. **GATE de imagem** (contar
   braços/mãos, texto desenhado, anacronismos, rosto em luz divina = NÃO).
3. **Clipes (27):** kling-3-omni image2video **std + generateSound=false**, 5s,
   startFrame = frame aprovado, prompt = `motion_prompt` + STYLE. **Ondas de 8**
   (PARALLEL_LIMIT_EXCEEDED). Registrar em `videos-jobs.tsv`. **GATE de vídeo**.
4. **Capas:** padrão madura cinematográfico (CLAUDE.md §3.11): letras 3D metálicas
   **azul-noite profundo com brilho prata-estrela** + trim DOURADO grosso, título
   "O NASCIMENTO DE JESUS" empilhado em 2 linhas, EXACTLY ONCE, acentos PT-BR,
   **SEM byline/canal/watermark**. Arte: noite de Belém, estábulo iluminado, estrela
   radiante, Maria/José/manjedoura em silhueta dourada.
5. **Montagem local:** `./assemble.sh` → `o-nascimento-de-jesus_final.mp4` →
   QA (§9 do CLAUDE.md) → concatenar intro oficial (§8.3) → COM-INTRO.

## Vozes (ElevenLabs v3, stability 1.0)

| Papel | Voz | voice_id |
|---|---|---|
| Narrador | Lucas – Deep & Profound | GIuLCSVfgJaUuh7hYOY8 |
| Maria | Taciana (BR, jovem, calorosa) | oqUwsXKac3MSo4E51ySV |
| Anjo | Adam Borges (solene) | ZqE9vIHPcrC35dZv0Svu |
| Pastores (fala Lc 2:15) | Eduardo J. (gaúcho RS) | S6JRAR6bdDn0imFzAhjA |
| Magos (fala Mt 2:2) | Felipette | JtRtm0OrgcgUP6oMWQgc |
| José de Nazaré | **não fala** (fidelidade: a Bíblia não registra palavras dele) | — |

Revisão de ouvido obrigatória: sotaque pt-BR (v3 puxa pt-PT), 1ª palavra de cada
request (distorção), tags não lidas em voz alta.
