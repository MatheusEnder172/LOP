# Prompts para os colegas — gráficos padronizados da seção de Resultados

Dois prompts: **A** (uma figura qualquer no padrão) e, mais abaixo, **B** (gerar a minha parte de Resultados: os 16
ensaios da minha modelagem contra o white-box, em gráficos individuais, 2x2 e 4x4).

## Prompt A — uma figura qualquer

Como usar: abra o Claude Code (ou outra IA com acesso à pasta do projeto) na pasta `Codigo_v4`, cole o texto do bloco abaixo e
preencha só a parte **[O QUE EU QUERO]** no começo. O resto é fixo.

```text
Você vai me ajudar a gerar uma figura para a seção de Resultados do nosso TCC (LOP, UFMG, Engenharia Química: modelagem
híbrida serial, rede neural + balanço populacional, da lixiviação de concentrado ustulado de zinco). O grupo adotou um
PADRÃO ÚNICO de gráficos para que todas as figuras do relatório pareçam feitas pela mesma pessoa. Siga o padrão à risca.

[O QUE EU QUERO]
Figura: <descreva o que deve aparecer, ex.: "curvas X_Zn(t) dos 4 modelos para os ensaios 7, 8 e 14">
Dados: <arquivos CSV/saídas de onde sair, ou "procure em Código/outputs/">
Número da figura no relatório: <ex.: 14>

PASSO 1 — Leia antes de escrever qualquer código (pasta Documento/padrao_graficos/):
 1. padrao_graficos_lop.py        módulo do padrão (fonte da verdade: cores, tamanhos, funções)
 2. exemplo_figura_padrao.py (3 painéis) e exemplo_figura_painel_unico.py (barras, 1 painel, ensaios de teste
    cego): figuras-modelo; a sua deve ter a mesma cara. Em figura só de barras use pg.legenda_topo(..., barras=True).
 3. exemplos/figura_padrao_exemplo.png, exemplos/figura_painel_unico_exemplo.png e exemplos/paleta_lop.png
    (abra e olhe as imagens)
 4. GUIA_PADRAO_GRAFICOS.md       paleta e decisões do grupo
Use `import padrao_graficos_lop as pg` (adicione a pasta ao sys.path). NÃO reimplemente o estilo, NÃO use plt.style,
NÃO escolha cores por conta própria e NÃO altere o módulo; se faltar algo, me diga o que falta.
(exemplo_figura_padrao.py importa `dados` de exemplos_estilos.py só para carregar os dados reais; você não precisa
disso: leia os SEUS dados dos arquivos que eu indiquei.)
Se aparecer o aviso "Times New Roman não encontrada", PARE e me avise: sem a fonte a figura não segue o padrão.

PASSO 2 — Regras obrigatórias (o módulo já cumpre a maioria; confira todas no final):
 - Estilo C: Times New Roman (a fonte do Word), caixa completa, grade pontilhada leve, ticks para dentro.
 - Largura 16 cm (pg.LARGURA_CM) ou 7,8 cm (pg.LARGURA_MEIA_CM), 300 DPI, e SEMPRE PNG + PDF (pg.salvar faz os dois).
   Não use bbox_inches="tight" (muda a largura).
 - SEM título dentro da figura. O "Figura N – título" e a "Fonte:" ficam na legenda do Word.
 - Vírgula como separador decimal nos eixos e em qualquer número escrito na figura (pg.num(0.0657, 3) -> "0,066").
 - Figura com 2 ou mais painéis: rotule (a), (b), (c) em negrito no canto superior esquerdo (pg.rotular_paineis).
   Figura com painel único: NÃO coloque rótulo.
 - Altura sugerida (largura 16 cm): 7 a 9 cm para 1 painel; 9 a 11 cm para 1x2; 14 a 17 cm para 2x2. As margens do
   módulo já são em cm e acomodam o rótulo do eixo x; só mexa em left/bottom/top/hspace/wspace se algo for cortado.
 - Eixo de categorias (ensaios): rótulo pg.ROTULOS["ensaio"]. Partição: marque os ensaios de teste cego com asterisco
   (pg.rotulos_ensaio(ensaios, cegos=[7, 8, 14])) e me diga o texto da nota (pg.NOTA_TESTE_CEGO = "* ensaio de teste cego") para a legenda do Word. Treino não leva marca.
   Se o gráfico mostra a partição de outro jeito (ex.: painéis separados), diga qual no seu relatório final.
 - Legenda numa linha só no topo, fora dos painéis (pg.legenda_topo). Nada de legenda cobrindo dado.
 - Rótulos de eixo SEMPRE com unidade e símbolo: use pg.ROTULOS (tempo, X_Zn, RMSE, etc.). Símbolos em mathtext com
   texto reto nos índices: $X_{\mathrm{Zn}}$, $C_{\mathrm{A0}}$. Letras gregas como caractere Unicode (η), fora do mathtext.
 - Experimental = círculo preto com miolo branco (pg.pontos_exp), sempre por cima das curvas.
 - Fundo branco, sem sombra, sem 3D, sem barras de erro inventadas. Faixa de comitê (mín–máx) só se eu pedir, e
   escrita como "variação entre membros do comitê", nunca como intervalo de confiança.
 - Se a cinética acontece quase toda no 1º minuto e as curvas ficam coladas, use pg.inserto_zoom (quadro ampliado).

PASSO 3 — Paleta FIXA (cor + linha + marcador + hachura; a cor nunca é o único jeito de distinguir):
 White-box (Fabrício)  laranja   #E69F00   tracejada --      quadrado  ///
 White-box (novo)      azul      #0072B2   pontilhada :       triângulo ...
 MLP pura              verde     #009E73   traço-ponto -.     losango   xxx
 Híbrido serial        rosa      #CC79A7   sólida (mais grossa) círculo  (sem hachura)
 PINN                  vermelhão #D55E00   traço-ponto-ponto   triângulo p/ baixo  \\\
 Híbrido paralelo      azul-claro #56B4E9  traço longo         cruz cheia          ++
 Extra (η, T, variante que não seja modelo): cinza #6E6E6E via pg.serie_extra(0). Só existe uma; se precisar de
   mais, me avise.
 Essas cores valem para o relatório inteiro: o mesmo modelo tem sempre a mesma cor, em qualquer figura. A ordem da
 legenda e das barras é sempre: Fabrício, novo, MLP pura, PINN, paralelo, serial (só os que aparecem). Não use amarelo, vermelho puro nem verde-limão.

PASSO 4 — Rigor com os dados (é um relatório técnico, números têm de ser rastreáveis):
 - Todo número da figura vem de arquivo existente em Código/outputs/ ou de um cálculo no seu script. Não invente nem
   "arredonde para ficar bonito". Se um valor que preciso não existir, diga qual falta.
 - Protocolo do projeto: treino = 13 ensaios (91 pontos, t > 0); teste cego = ensaios 7, 8 e 14 (21 pontos); global = 112.
   Marque sempre qual partição está no gráfico. O teste cego JÁ foi visto uma vez; não o use para escolher nada novo.
 - Para métricas, RMSE de X_Zn em pontos percentuais (p.p.) = 100 x RMSE.
 - Não retreine modelos nem altere scripts existentes. Só leia os modelos/saídas congelados.

PASSO 5 — Entrega:
 - Um script gerar_fig_<numero>_<descricao>.py na pasta da etapa em Código/etapas/ de onde vêm os dados (ex.: dados
   de outputs/etapa_4_2_avaliacao_indomain/ -> etapas/etapa_4_2_avaliacao_indomain/). Na dúvida, me pergunte qual etapa.
 - Saídas em Código/outputs/<etapa>/: fig_<numero>_<descricao>.png e .pdf, e um CSV com os números plotados.
 - Nunca apague nem sobrescreva arquivo existente: se for substituir algo, mova o antigo para uma pasta old/ com README.
 - Registre no DEVLOG.md na raiz, no mesmo formato das entradas existentes (leia as últimas antes de escrever).
 - Não faça commit. Eu faço.

PASSO 6 — Confira ANTES de me entregar e me diga o resultado de cada item (abra o PNG de verdade e olhe):
 [ ] largura 16 cm (ou 7,8) e 300 DPI; existem o .png e o .pdf
 [ ] nenhum título na figura; fonte Times New Roman; vírgula decimal em todos os números
 [ ] (a), (b), (c) presentes se houver 2+ painéis (nenhum rótulo se for 1 painel); legenda no topo, sem cobrir dados;
     nenhum rótulo cortado ou sobreposto (olhe as bordas da imagem)
 [ ] cores, linhas e marcadores iguais à paleta; ordem da legenda correta
 [ ] eixos com símbolo e unidade; escala dos eixos honesta (sem cortar o zero das barras)
 [ ] em preto e branco ainda dá para distinguir as séries (linha/marcador/hachura)
 [ ] cada número do gráfico rastreável a um arquivo; partição (treino / teste cego / global) indicada
Se algum item falhar, corrija e gere de novo antes de me entregar. No fim, me diga em 3 linhas o que a figura mostra e
o que NÃO dá para concluir dela (limitações), sem exagerar o resultado.

Se você NÃO conseguir ler os arquivos do padrão: use matplotlib com font.family=Times New Roman, tamanho 10, figsize de
16 cm de largura, dpi=300, savefig em PNG e PDF (pdf.fonttype=42), grade tracejada pontilhada alpha 0,25, ticks para
dentro, caixa completa, vírgula decimal, as cores/linhas/marcadores da tabela acima, e me avise que não usou o módulo.
```

## Prompt B — a minha parte de Resultados (16 ensaios, minha modelagem × white-box novo)

Como usar: abra o Claude Code na pasta `Codigo_v4`, cole o bloco abaixo e preencha só a parte **[MINHA MODELAGEM]**.

```text
Você vai me ajudar a gerar os gráficos da MINHA parte de Resultados do nosso TCC (LOP, UFMG, Engenharia Química:
lixiviação de concentrado ustulado de zinco; modelagem híbrida). Cada integrante do grupo faz a sua modelagem e todos
usam o MESMO modelo de gráfico, para depois juntarmos as quatro numa comparação com as mesmas cores.

[MINHA MODELAGEM]
Modelagem: <pinn | paralelo | serial>
Onde está o meu modelo treinado e congelado (pasta/arquivos e como carregar): <...>
Observação (ex.: meu modelo não aceita t = 0; roda em MATLAB; usa outra função de predição): <...ou "nenhuma">

PASSO 1 — Leia (pasta Documento/padrao_graficos/): GUIA_PADRAO_GRAFICOS.md (seção "Parte de Resultados por modelagem"),
resultados_lop.py, template_resultados_meu_modelo.py e o exemplo já preenchido
Código/etapas/etapa_4_2_avaliacao_indomain/gerar_resultados_serial.py. Abra também as imagens em
Código/outputs/resultados_por_modelagem/serial/ (fig_serial_ensaio_09.png, fig_serial_2x2_ensaios_05_08.png e
fig_serial_4x4_todos.png): os meus devem ficar iguais a elas, só mudando a curva e a cor da modelagem.

PASSO 2 — Faça:
 1. Copie template_resultados_meu_modelo.py para a pasta da minha etapa em Código/etapas/ (me pergunte qual, se não
    souber) como gerar_resultados_<modelagem>.py. Troque CHAVE pela minha modelagem.
 2. Preencha SÓ carregar_meu_modelo() e prever(modelo, ca0, eta, t): X_Zn em fração (0 a 1), mesmo tamanho de t, t em min,
    T = 40 °C. Não altere resultados_lop.py nem padrao_graficos_lop.py. Se o meu modelo não rodar em Python, peça-me um
    CSV de curvas densas (ensaio, t_min, XZn, 16 ensaios, grade resultados_lop.T_DENSO) e use CSV_DAS_CURVAS.
 3. NÃO retreine nada e não altere scripts existentes: só leia o modelo congelado. O teste cego (ensaios 7, 8, 14) já foi
    visto; relate os números como estão, sem escolher nada novo com base neles.
 4. Rode. Saída automática em Código/outputs/resultados_por_modelagem/<modelagem>/: 16 gráficos individuais, 4 gráficos
    2x2, 1 gráfico 4x4 (PNG + PDF), metricas_resumo.csv, metricas_por_ensaio.csv, dados_plotados.csv e
    curvas_<modelagem>.csv.
 5. Nunca apague nem sobrescreva arquivo existente (mova o antigo para old/ com README). Registre no DEVLOG.md no formato
    das entradas existentes. Não faça commit.

PASSO 3 — Confira antes de me entregar (abra de verdade pelo menos o individual do ensaio 9, um 2x2 e o 4x4):
 [ ] os valores de metricas_resumo.csv do white-box novo são IGUAIS aos do exemplo serial (RMSE treino 6,82; teste cego
     7,80; global 7,02 p.p.). Se não forem, algo está errado no white-box ou nos dados: pare e me avise.
 [ ] 16 ensaios (91 pontos de treino + 21 de teste cego = 112); ensaios 7, 8 e 14 com asterisco no 2x2 e no 4x4
 [ ] a curva da minha modelagem está na cor do padrão; white-box azul pontilhado; limite estequiométrico pontilhado fino
 [ ] a curva da modelagem sai de t = 0 e, se passar do limite estequiométrico, me diga em quais ensaios
 [ ] nada cortado, legenda no topo, vírgula decimal, sem título dentro da figura
No fim, me entregue: (1) a tabela metricas_resumo.csv em texto; (2) em 3 linhas, onde a minha modelagem acerta e onde
erra mais (cite ensaios); (3) o que esses gráficos NÃO permitem concluir (ex.: só 3 ensaios cegos, todos dentro do
domínio de treino; sem teste de extrapolação). Não exagere o resultado.
```

Para a comparação final (depois que os quatro tiverem rodado): `rl.juntar_curvas(...)` lê os `curvas_<modelagem>.csv` de cada
um, e `gerar_comparacao_final_2x2.py` desenha as curvas de todos num 2x2 por ensaio (formato escolhido para a comparação
final), cada modelagem na sua cor. Por isso é importante que `curvas_<modelagem>.csv` e `dados_plotados.csv` fiquem na pasta
de saída, sem renomear.

## Depois de gerar, no Word

- Legenda no padrão ABNT: **Figura N – título** em cima e **Fonte: elaborado pelos autores** embaixo, fora da imagem.
- Inserir o **PNG** (ou o PDF, se o Word aceitar) na largura de 16 cm, sem esticar (100%).
- Texto novo ou alterado fora de Métodos entra em fonte **vermelha**, como combinado.
