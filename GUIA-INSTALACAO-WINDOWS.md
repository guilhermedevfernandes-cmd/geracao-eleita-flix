# Guia de instalação — produzir episódios no notebook Windows

> Passo a passo para configurar o notebook Windows do ZERO e produzir episódios do
> Geração Eleita Flix. Feito para quem não é da área de tecnologia — é copiar e colar.
> Tempo estimado: 30-40 minutos, uma única vez.

## Como funciona (entenda antes de instalar)

Quem gera as imagens, os vídeos e as vozes são serviços na nuvem (OpenArt, HiggsField,
ElevenLabs) — o notebook não precisa ser potente. O que você instala aqui é:

1. **Claude** — o "diretor de produção" com quem você conversa;
2. **três ferramentas de apoio** (Git, Python, ffmpeg) que ele usa para baixar e montar
   o vídeo final;
3. **a pasta do projeto**, que contém o manual completo do canal (`CLAUDE.md`) — é ele
   que garante que o episódio sai no padrão aprovado.

Seu papel na produção: **pedir o episódio e REVISAR** o que o Claude mostrar (imagens,
vídeos, áudio). Ele sabe as regras, mas o olho final é humano.

---

## Passo 0 — Contas (fazer junto com o Guilherme)

- [ ] **Conta Claude própria** (claude.ai) — plano Pro ou Max. Não usar a conta dele
      (a Anthropic proíbe compartilhar, e os limites de uso são por conta).
- [ ] **Conta GitHub** (github.com) — gratuita. Depois de criada, o Guilherme te adiciona
      como colaboradora do repositório privado `geracao-eleita-flix`
      (no GitHub: repositório → Settings → Collaborators → Add people).
- [ ] **Logins das plataformas de geração** (anotar com ele): OpenArt, HiggsField e a
      chave da API do ElevenLabs. Os créditos são compartilhados do casal — combinem o uso.

## Passo 1 — Instalar o Claude (app para Windows)

1. Baixe em **https://claude.com/download** (Windows 10/11).
2. Instale e entre com a SUA conta Claude.

## Passo 2 — Instalar Git, Python e ffmpeg

1. Clique no menu Iniciar, digite **PowerShell**, clique com o botão direito →
   **Executar como administrador**.
2. Cole as três linhas abaixo (uma de cada vez, dando Enter e aguardando terminar):

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.13 -e
winget install --id Gyan.FFmpeg -e
```

3. **Feche e abra o PowerShell de novo** (agora pode ser normal, sem administrador) e
   confira se os três respondem com um número de versão:

```powershell
git --version
python --version
ffmpeg -version
```

> Se algum `winget install` reclamar que não achou o pacote, procure o nome certo com
> `winget search ffmpeg` (ou `git` / `python`) e instale o ID que aparecer.

## Passo 3 — Baixar a pasta do projeto (GitHub Desktop)

1. Instale o GitHub Desktop: `winget install --id GitHub.GitHubDesktop -e`
   (ou baixe em https://desktop.github.com).
2. Abra, entre com a sua conta GitHub (já adicionada como colaboradora no Passo 0).
3. **File → Clone repository** → aba **GitHub.com** → escolha
   `geracao-eleita-flix` → clone em `Documentos` (anote o caminho da pasta).
4. **Sempre antes de produzir**: abra o GitHub Desktop e clique em **Fetch/Pull origin**
   para receber as novidades (roteiros novos, lições novas no manual).

## Passo 4 — Guardar a chave do ElevenLabs

No PowerShell (normal), cole as duas linhas abaixo — troque `COLE_A_CHAVE_AQUI` pela
chave que o Guilherme te passar (começa com `sk_`):

```powershell
New-Item -ItemType Directory -Force "$HOME\.config\gerecao-eleita-flix" | Out-Null
Set-Content "$HOME\.config\gerecao-eleita-flix\elevenlabs.env" 'ELEVENLABS_API_KEY=COLE_A_CHAVE_AQUI'
```

Pronto — os scripts do projeto leem a chave desse arquivo automaticamente.
(Nunca cole essa chave em site, chat ou e-mail.)

## Passo 5 — Conectar OpenArt e HiggsField no Claude

1. Entre em **claude.ai** no navegador, com a sua conta.
2. Vá em **Settings → Connectors** (Configurações → Conectores).
3. Procure e conecte **OpenArt** → faça login com a conta OpenArt do casal.
4. Procure e conecte **Higgsfield** → idem.
5. No app Claude do Windows, confira em Settings → Connectors que os dois aparecem.

## Passo 6 — Primeiro teste

1. Abra o app **Claude** → abra a pasta do projeto (a que você clonou no Passo 3).
2. Digite: `Leia o CLAUDE.md e me diga em 5 linhas como funciona a produção de um episódio.`
3. Se ele responder citando o pipeline (imagens → revisão → vídeos → áudio ElevenLabs →
   montagem → COM-INTRO), está tudo pronto. 🎉

## Como pedir um episódio (exemplos)

```
Produza o EP13 sobre [história bíblica], seguindo o CLAUDE.md.
Comece pelo roteiro com as referências bíblicas e o checklist do
FIDELIDADE-BIBLICA.md, e me mostre para aprovar antes de gerar imagens.
```

```
Continue o EP13: as imagens da cena 2 que você me mostrou estão aprovadas,
menos a do plano 2b (o personagem ficou com a roupa errada — regenere).
```

O Claude vai te mostrando cada etapa. **Regra de ouro: nada avança sem você olhar** —
confira personagens (braços! mãos!), estilo, e ouça a narração inteira antes da montagem.
O checklist completo do que olhar está nas seções 9 e 10 do `CLAUDE.md`.

O vídeo final aparece na pasta do episódio como `EP13-COM-INTRO-....mp4`.

## Ao terminar um episódio

Peça ao Claude: `Commite e suba os arquivos leves do EP13 (roteiro, TSVs, scripts e as
lições novas do CLAUDE.md).` Assim o Mac do Guilherme recebe tudo no próximo Pull.

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `ffmpeg não é reconhecido` | Feche e reabra o PowerShell/Claude (o PATH atualiza ao reabrir). Persistindo, reinstale o Passo 2. |
| Claude diz que não tem acesso ao OpenArt/HiggsField | Refazer Passo 5; conferir que os conectores estão ativos na MESMA conta logada no app. |
| Erro `ELEVENLABS_API_KEY não configurada` | Refazer Passo 4 (conferir se a chave foi colada certa, sem aspas extras). |
| Geração de vídeo falha com `PARALLEL_LIMIT_EXCEEDED` | Normal — máximo 8 vídeos por vez. Peça ao Claude para submeter em ondas (ele sabe). |
| Créditos acabaram (OpenArt/HiggsField/ElevenLabs) | Falar com o Guilherme antes de continuar. |
| Episódio ficou sem a vinheta de abertura | Cobre o Claude: "gere a versão COM-INTRO" (é obrigatória, seção 8.3 do CLAUDE.md). |
