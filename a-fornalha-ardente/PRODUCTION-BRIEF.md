# Geração Eleita Flix — briefing mestre de alta qualidade

Este briefing vale para todo episódio novo. Os episódios antigos permanecem como arquivo do pipeline v1; nenhuma nova produção deve copiar suas limitações.

## Objetivo editorial

Produzir um curta bíblico infantil com acabamento de longa-metragem 3D, duração real próxima de cinco minutos, emoção clara, fidelidade ao texto bíblico, personagens com voz própria e desenho de som cinematográfico.

O resultado não pode parecer uma sequência de ilustrações narradas. A história precisa acontecer diante da criança: personagens tomam decisões, falam, reagem, escutam, erram e mudam.

## Público e linguagem

- Público principal: crianças de 5 a 11 anos assistindo com a família.
- Idioma exclusivo: português brasileiro (`pt-BR`).
- Vocabulário simples sem infantilizar demais.
- Frases naturais no Brasil. Evitar construções, pronúncias e vozes de português europeu.
- Trechos curtos que o detector não consegue classificar exigem revisão linha a linha
  e `./approve-script.sh --confirm-ambiguous-pt-br`; não há aprovação silenciosa.
- Perigo e tensão podem existir, mas sem violência gráfica, terror ou sofrimento prolongado.
- Deus é representado por voz, luz, vento, ambiente e reação dos personagens; nunca por uma figura humana.

## Duração e ritmo obrigatórios

- Duração final: 285 a 315 segundos.
- Ritmo de voz de referência: 138 palavras por minuto.
- Estrutura: 34 a 46 planos, normalmente de 6 a 10 segundos.
- Nenhum beat pode exigir mais de 11,2 segundos de um clipe de 10 segundos.
- Falas longas devem ser divididas em novos planos; a montagem não usará câmera lenta excessiva para escondê-las.
- O gancho precisa surgir nos primeiros 12 segundos.
- A promessa emocional ou pergunta central precisa estar clara até 30 segundos.
- O clímax deve receber mais espaço, contraste, VFX e desenho de som que as cenas expositivas.
- O encerramento deve concluir a transformação e a verdade bíblica sem soar como uma palestra.

## Arquitetura narrativa

Cada história deve conter pelo menos seis beats com função diferente:

1. Gancho visual e emocional.
2. Mundo e desejo do protagonista.
3. Chamado ou conflito.
4. Escolha errada, resistência ou escalada.
5. Consequência e ponto de maior tensão.
6. Encontro com a graça de Deus e mudança.
7. Ação transformada.
8. Resolução e aplicação curta.

“Mostrar antes de explicar” é a regra. O narrador conecta tempo, lugar e passagens difíceis; ele não deve dizer aquilo que imagem, ação ou diálogo já mostram.

## Dublagem e elenco

- Usar no mínimo quatro vozes distintas em cada episódio quando a história oferecer personagens suficientes.
- Pelo menos 25% das palavras faladas devem pertencer aos personagens, e não ao narrador.
- Narrador, protagonista, voz de Deus e personagens de apoio importantes recebem identidades vocais diferentes.
- Cada `voice_id` precisa ter uma amostra gerada em `audio/voice-tests/`.
- Uma pessoa deve ouvir a amostra e executar `./approve-voice.sh <key>`. O comando
  marca `voice_approved=yes` e vincula a aprovação ao `voice_id`, ao texto de teste
  e aos hashes da amostra; qualquer mudança invalida a aprovação.
- `./gen-narr.sh` deve falhar se a voz estiver pendente, sem ID, com locale diferente de `pt-BR` ou se a chave estiver errada.
- Nunca substituir automaticamente uma voz ausente pelo narrador.
- A aprovação verifica sotaque brasileiro, dicção, idade aparente, emoção, estabilidade e ausência de som robótico.

## Direção visual

- Estética: animação 3D estilizada premium, sem imitar nominalmente um estúdio ou artista.
- Cada cena define tipo de plano, lente implícita, profundidade, ação principal, reação, luz, clima e geografia.
- Usar no mínimo oito tipos de plano ao longo do episódio.
- Alternar escala: establishing, planos médios, close-ups emocionais, POV, low-angle, aerial, tracking e detalhes.
- Toda composição precisa de primeiro plano, plano médio e fundo quando a cena permitir.
- Personagens mantêm rosto, idade, proporções, roupa, acessórios e paleta.
- `refs` é uma lista branca visual: todo ser humano visível deve estar listado; `refs=-`
  exige um plano estritamente ambiental, sem pessoas, humanoides, silhuetas ou extras.
- Deus nunca recebe rosto, corpo, mãos, sombra ou silhueta. Sua presença visual usa
  exclusivamente luz branca-dourada, raios volumétricos, vento e reação do ambiente.
- Não inserir roupas, objetos, tecnologia, exploradores ou arquitetura modernos em
  cenas bíblicas, salvo quando o prompt pedir explicitamente.
- Referência de personagem é sempre uma única figura em pose neutra; nunca um mosaico.
- Referências precisam ter no mínimo 1440×1920; frames e clipes, no mínimo 1920×1080.
- Clipes devem ser MP4/MOV reais em 24–60 fps; vídeos renomeados como imagem e
  animações de baixa cadência são reprovados.
- Cada referência, frame e clipe revisado recebe aprovação vinculada ao hash exato;
  regenerar ou trocar o arquivo invalida essa aprovação.
- Câmera se move por uma razão narrativa. Evitar “slow push-in” repetido como solução universal.
- Planos de ação precisam de entrada, desenvolvimento e pose final utilizável no corte seguinte.

## VFX e espetáculo

No mínimo 25% dos planos devem ter VFX dedicado. O efeito precisa servir à história:

- céu, nuvens volumétricas, chuva, relâmpagos distantes e espuma do mar;
- partículas, poeira, névoa, água, vento, tecido e detritos com física coerente;
- luz divina, feixes volumétricos e mudança de cor com reverência;
- escala e profundidade para cidades, tempestades, navios, criaturas e multidões;
- transições motivadas por água, luz, movimento de câmera ou formas semelhantes.

VFX não substitui atuação. O rosto e a reação do personagem continuam sendo o centro emocional.

## Desenho de som e música

- Pelo menos 70% das cenas recebem ambiência ou SFX planejado.
- Cada camada deve combinar ambiente, ação em primeiro plano e profundidade espacial.
- Não gerar vozes ou música dentro do modelo de vídeo.
- Narração e diálogos ficam em arquivos separados por cena.
- SFX ficam em `audio/sfx/NN.wav`.
- Música fica em `audio/bgm.mp3`, sem voz.
- Toda trilha, gerada ou externa, precisa ser ouvida e vinculada com
  `./approve-music.sh`; mudar o arquivo ou o prompt invalida a aprovação.
- A montagem reduz automaticamente a trilha sob as falas, normaliza o diálogo e limita o master.
- Silêncio intencional é permitido e deve ser marcado com `-`; não é ausência de planejamento.

## Fidelidade bíblica

- Registrar a passagem bíblica usada antes de escrever.
- Não atribuir a Deus, profetas ou reis frases que mudem o sentido do texto.
- Diálogos adaptados podem simplificar a linguagem, mas não inventar doutrina.
- Manter as decisões moralmente difíceis do protagonista; não transformar personagens bíblicos em heróis perfeitos.
- A aplicação final nasce da transformação mostrada na história.

## Gates de aprovação

1. `./validate.sh script`: estrutura, cinco minutos, riqueza narrativa, câmera, VFX, SFX e PT-BR.
2. `./make-roteiro.sh`: leitura e aprovação humana antes de gastar créditos.
3. `./approve-script.sh`: a aprovação fica vinculada aos TSVs e ao briefing lidos.
4. `./gen-voice-tests.sh` + `./approve-voice.sh`: audição humana de todo o elenco.
5. `./gen-narr.sh`: fixa a duração real antes de aprovar qualquer clipe.
6. `./gen-sheets.sh` + lote OpenArt MCP + `./register-openart.sh reference all` + aprovação: identidade e figurino.
7. `./gen-frames.sh` + lote OpenArt MCP + `./register-openart.sh frame all` + aprovação: composição e continuidade.
8. `./gen-clips.sh` + lote OpenArt MCP + `./register-openart.sh clip all`, ou produção manual + `./register-clips.sh`: animação vinculada ao frame e ao prompt.
9. `./approve-visual.sh clip all`: revisão de morphing, física, câmera, VFX e stretch contra o áudio real.
10. `./gen-sfx.sh`, trilha e `./approve-music.sh`: desenho de som.
11. `./validate.sh assembly`: presença, aprovações e limite de stretch.
12. `./assemble.sh`: render atômico, master 1080p e relatório com proveniência.

Se qualquer gate reprovar, o episódio não avança.
