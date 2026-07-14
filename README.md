# 🎬 Geração Eleita Flix — Central de Produção

Curtas **cristãos infantis** em animação 3D cinematográfica premium (16:9), com
histórias bíblicas de **cinco minutos reais**. Cada episódio fica numa subpasta própria.

> O contrato editorial e técnico está em [`PRODUCTION-BRIEF.md`](./PRODUCTION-BRIEF.md).
> Todo episódio novo usa o pipeline v2; as pastas antigas continuam como arquivo do v1.

---

## 🚀 Novo episódio

```bash
./scripts/new-episode.sh jonas-e-o-grande-peixe "Jonas e o Grande Peixe"
cd jonas-e-o-grande-peixe
```

O scaffold inclui gates de duração, multivoz, sotaque PT-BR, riqueza narrativa,
VFX, SFX, variedade de câmera, continuidade e limite de câmera lenta.

### Gates que não podem ser ignorados

- Duração estimada e real entre 4min45s e 5min15s.
- 34–46 planos; falas longas são divididas, nunca escondidas com slow motion excessivo.
- No mínimo quatro vozes e 25% de diálogo direto.
- Toda voz é marcada `pt-BR`, recebe amostra e precisa de aprovação humana.
- Falas linguisticamente ambíguas exigem confirmação PT-BR explícita no roteiro.
- Voz ausente ou não aprovada interrompe a produção; não existe fallback para o narrador.
- No mínimo 25% dos planos com VFX e 70% com SFX/ambiência.
- No mínimo oito tipos de plano/câmera.
- Referências e frames abaixo da resolução 2K, ou clipes abaixo de 1080p/24 fps, são rejeitados.
- Referências, frames e clipes precisam de aprovação humana vinculada ao hash exato.
- O master só substitui a versão anterior após validar sessão, timeline, stems,
  roteiro, aprovações e todas as mídias usadas.

---

## 🔧 Pipeline v2

```bash
./validate.sh script       # reprova roteiro simples, curto ou sem elenco
./make-roteiro.sh          # documento legível para aprovação
./approve-script.sh        # vincula a aprovação ao roteiro realmente lido
./gen-voice-tests.sh       # audição obrigatória de sotaque brasileiro
./approve-voice.sh <key>   # vincula a aprovação à amostra realmente ouvida
./gen-narr.sh              # dublagem multivoz e duração real antes dos visuais
./gen-sheets.sh            # prepara lote OpenArt de referências
./register-openart.sh reference all # registra resultados do lote
./approve-visual.sh reference all  # depois de revisar identidade e figurino
./gen-frames.sh            # prepara lote OpenArt de keyframes
./register-openart.sh frame all     # registra resultados do lote
./approve-visual.sh frame all      # depois de revisar composição e continuidade
./make-kit.sh              # guia detalhado para animação manual
./gen-clips.sh             # prepara lote OpenArt de animações
./register-openart.sh clip all      # registra resultados do lote
./register-clips.sh        # obrigatório após baixar clipes manuais
./approve-visual.sh clip all       # depois de revisar física, câmera e morphing
./gen-sfx.sh               # ambiência e efeitos por cena
./gen-score.sh             # trilha opcional; também aceita audio/bgm.mp3 externo
./approve-music.sh         # obrigatório quando existir trilha, gerada ou externa
./validate.sh assembly     # mídia completa e stretch seguro
./assemble.sh              # ducking, loudness, limiter e master 1080p
```

> **`characters.tsv`, `scenes.tsv` e `meta.env` são as fontes únicas de verdade.**
> O roteiro legível, os prompts, o áudio e a montagem derivam desses arquivos.

### Geração visual paralela com OpenArt MCP

O Cursor precisa ter o servidor `openart` conectado em
`https://mcp.openart.ai/mcp` e autenticado por OAuth. Cada `gen-*.sh` visual
gera um manifesto em `build/openart/` com todas as tarefas pendentes. O agente
executa até `OPENART_CONCURRENCY` chamadas MCP simultâneas, salva os resultados
nos caminhos declarados e roda `register-openart.sh` para normalizar, validar e
registrar os hashes.

O OAuth permanece no Cursor; os scripts não armazenam tokens. O OpenArt MCP
cobre imagens e vídeos. Vozes, SFX e trilha usam a API ElevenLabs
(`ELEVENLABS_API_KEY` em `~/.config/gerecao-eleita-flix/elevenlabs.env`).

---

## 📁 Estrutura de cada episódio

```
<slug>/
├─ meta.env          # contrato: duração, idioma, qualidade, modelos e mixagem
├─ characters.tsv    # elenco: voz, locale, aprovação PT-BR e referência visual
├─ scenes.tsv        # roteiro técnico: ato, plano, fala, hold, VFX, SFX e transição
├─ roteiro.md        # ⟵ documento LEGÍVEL (gerado; aprove ANTES de gerar imagens)
├─ KIT-PRODUCAO.md   # ⟵ guia detalhado para animação de cada plano
├─ assets/           # <key>_ref.png  (referências de personagem)
├─ frames/           # 01.png … NN.png (keyframes cinematográficos)
├─ clips/            # 01.mp4 … NN.mp4 (planos de 10s)
├─ audio/            # falas, voice-tests/, sfx/ e bgm.mp3
├─ approvals/        # aprovações vinculadas do roteiro, visuais e trilha
├─ logs/             # consumo persistente dos provedores
├─ build/            # timeline, stems e relatório técnico
├─ _pipeline/        # cópia versionada dos validadores e helpers usados pelo episódio
└─ *.sh              # comandos auto-contidos do episódio
```

---

## ✅ Lições aprendidas (NÃO repetir os erros)

1. **Referência = UMA figura única e limpa.** Nunca um "character sheet" com várias poses
   — o Nano Banana **clona** o personagem (saíam dois Noés na mesma cena). O `gen-sheets.sh`
   já força figura única (corpo inteiro, pose neutra, fundo liso); as descrições em
   `characters.tsv` devem focar só no personagem, sem "multiple poses".

2. **Roteiro.md vem PRIMEIRO.** É o documento legível pra aprovar antes de gastar geração.
   Sempre rodar `make-roteiro.sh` e revisar antes do `gen-frames.sh`.

3. **Numeração sequencial `01…NN`** nos frames E nos clipes — o validator reprova lacunas,
   duplicatas e sufixos antes da geração.

4. **Deus é só VOZ, nunca retratado.** Cenas com Deus mostram luz/raios e o personagem
   olhando pra cima. Em `characters.tsv`, a "voz de Deus" tem `voice_id` mas sem descrição
   (não gera referência). Vilões/perigo sempre "ameaçador-fofo", clímax sem violência gráfica.

5. **O manifesto define a correspondência entre cena e saída.** Nunca associe
   resultados pela ordem da galeria. Cada tarefa contém `task_id`, frame inicial,
   referências e `output.path`, evitando trocar cenas quando várias gerações
   OpenArt terminam fora de ordem.

6. **Vídeo:** **16:9** · **10s** · **"generate audio" DESLIGADO**. A montagem corta o
   material excedente e bloqueia qualquer stretch acima de 1,12x.

7. **Amostra de voz não prova locale sozinha.** O catálogo do provider de áudio não informa
   sotaque. Por isso `locale=pt-BR` e a audição humana são gates separados e obrigatórios.

---

## 📺 Episódios legados (pipeline v1)

| Episódio | Cenas | Status |
|---|---|---|
| `davi-e-golias/` | 17 | ✅ **Finalizado** (`DAVI_E_GOLIAS_final.mp4`) |
| `joao-batista/`  | 16 | 🟡 Frames prontos — faltam clipes |
| `noe-e-a-arca/`  | 40 | 🟡 40 frames + KIT prontos — **aguardando você animar os clipes** |
