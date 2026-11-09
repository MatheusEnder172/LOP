# Estado do documento (v10) e estrutura proposta para os Resultados

## 1. O que a v10 já tem

`Documento/RELATÓRIO FINAL LOP_v10.docx` (gerado em 08/11 por `adicionar_resultados_v10.py` a partir da v9).

**Em Métodos (cor normal), seção "MODELAGEM HÍBRIDA SERIAL" (parágrafos 514 a 595):** ideia do acoplamento, elementos do fenomenológico usados, problema inverso, base de dados e partição 13 + 3, arquitetura, função de perda e treinamento, critério de avaliação (validação cruzada), algoritmo de simulação e as duas restrições físicas.

**Em Resultados (vermelho), parágrafos 601 a 634, antes de CONCLUSÕES e depois dos quatro "AA" do grupo.** Hoje com 34 parágrafos, 2 tabelas e 4 figuras:

| Subseção atual | Conteúdo | Figura/Tabela |
| :-- | :-- | :-- |
| (abertura) | roteiro da seção | |
| Taxas de retração estimadas pelo problema inverso | RMSE 0,0137; teto 0,0142 | |
| Desempenho nos ensaios de treino e de teste cego | RMSE global 0,0157, teste cego 0,0202, comparações | Tabela 5.XX.1; Fig. 5.XX.1 e 5.XX.2 |
| Erro em condições não vistas | validação cruzada 0,0326 ± 0,0050, ensaios de borda | Fig. 5.XX.3 |
| Efeito das condições operacionais | patamar por η, efeito de C_A0 | Tabela 5.XX.2; Fig. 5.XX.4 |
| Consistência física | 1.681 condições | |
| Discussão e limitações | | |

**Apêndices (vermelho) que já têm detalhes e portanto NÃO se repetem nos Resultados:** B.5 (reconstrução das curvas), D.3 (treino do comitê, Tabela D.1), E.4 a E.7 (avaliação, linha de base, busca, teste cego, Tabelas E.3 a E.7, Figuras E.4 a E.11), E.8 a E.10 (perdas físicas, ajuste fino, síntese: nada superou a v2), E.11 (previsão a priori dos 4 ensaios novos).

## 2. O que muda com a decisão de 09/11

A seção de Resultados passa a ser **a apresentação da modelagem serial como uma das individualidades do grupo**, curta na parte de modelo e **mais longa e cuidadosa em treinamento e validação**. A v10 já cobre a maior parte com os números certos; o trabalho é **reestruturar, enxugar e aprofundar a validação**, não recalcular nada.

### Estrutura proposta (para discutir com o usuário antes de escrever; ele pode mudar)

Título: **MODELAGEM HÍBRIDA SERIAL** (mesmo da v10), subseções em ordem de leitura:

1. **Visão geral e protocolo de avaliação** (curto). Uma frase sobre o modelo (v2: comitê de 10 redes), os 13 ensaios de treino/validação cruzada, os 3 de teste cego, as métricas (R², RMSE, MAE sobre X_Zn, t ≥ 0,5 min). Define uma vez o "teto" e as duas referências (fenomenológico puro, v1). Sem repetir Métodos.
2. **Treinamento.** Alvos do problema inverso (RMSE 0,0137; teto 0,0142), ajuste do comitê (perda final 0,00039 a 0,00051; 928 épocas; ~1,3 min por membro; Tabela D.1 no apêndice) e desempenho nos 13 ensaios de treino (RMSE 0,0145; R² 0,995; 91 pontos). Mensagem: a rede reproduz os alvos, e o erro de ajuste é próximo do teto. Deixar claro que isso mede ajuste, não previsão.
3. **Validação cruzada por ensaio (evidência principal).** 4 dobras, 10 sementes, RMSE fora da dobra 0,0326 ± 0,0050 (EP 0,0016); por dobra; por ensaio (ensaios de borda 15, 10 e 6 são os piores); comparação com a v1 (0,183) e o teto (0,0142). Tabela por ensaio (treino × fora da dobra) e Figura 5.XX.3.
4. **Teste cego.** 3 ensaios, 21 pontos: RMSE 0,0202, R² 0,888; v1 0,0353; fenomenológico 0,0780. Por ensaio (7: pior que a v1). Comitê × membro único. Ressalva: o teste da v1 já fora visto; para a v2 é a primeira avaliação.
5. **Síntese do treino, da validação cruzada e do teste cego** (nova, proposta). Uma tabela e/ou figura que coloca lado a lado: teto 0,0142, treino 0,0145, validação cruzada 0,0326, teste cego 0,0202. Uma leitura honesta da diferença: por que o teste fica abaixo da validação cruzada (condições interiores) e que 3 ensaios não são conclusivos.
6. **Comportamento do modelo** (curto, enxuto da v10): efeito de η e C_A0 (Tabela 5.XX.2, Fig. 5.XX.4) e consistência física (1.681 condições). Pode virar um parágrafo cada, com a figura de mapa.
7. **Discussão e limitações** (curto): o que o ganho de 78% significa, o que não foi esclarecido (limite de dados × qualidade dos alvos; parâmetros no limite em 12 de 16 ensaios), domínio de validade, faixa do comitê não é intervalo de confiança.
8. **(Depois, extra)** Validação externa com os 4 ensaios novos. Ver `04_ensaios_novos_depois.md`. Não escrever agora.

### Análises opcionais que fortalecem "treinamento e validação" (só com autorização do usuário; usam dados já existentes)

- Tabela de RMSE **por dobra** da validação cruzada (dados em `fase_b2/finalistas_por_dobra.csv`; ver `03_numeros_e_fontes.md`).
- Erro **por instante** (início × patamar) nos 13 ensaios fora da dobra e nos 3 de teste: onde o modelo erra mais (já há indício: 0,5 min). Exige script novo que lê as curvas `finalistas_curvas.csv` / `curvas_fase_e_teste_cego.csv`.
- **Resíduos** (medido − previsto) versus tempo e versus η, para checar viés sistemático.
- Curva de perda por época: **verificar se existe salva** antes de prometer; se não existir, não retreinar (modelo congelado) e dizer que não há.

## 3. Como construir a v11 (técnica)

- Criar `Documento/ferramentas/reescrever_resultados_v11.py` (nome sugerido) que lê a v10 e grava a **v11** sem alterar a v10.
- O bloco a substituir vai do **segundo** título "MODELAGEM HÍBRIDA SERIAL" (o de Resultados, depois dos quatro "AA") até o título "CONCLUSÕES" (exclusive). O primeiro é o de Métodos e não se mexe. Usar `docx_utils.find_paragraph(doc, "MODELAGEM HÍBRIDA SERIAL", start=...)`; localizar o fim por "CONCLUSÕES".
- Reaproveitar do `adicionar_resultados_v10.py` as funções de carregar CSVs (`carregar`, `linha`, `pct`) e o padrão de `secao(w, heading, sub, fig, d)`; todo o novo passa por `pintar(...)` (vermelho).
- Conferir depois, por script: sem NUL, sem ids duplicados, comentários do Word preservados (a v10 tem 38), único acréscimo/remoção é o bloco de Resultados.
- Entregar um bloco por vez, como o usuário pediu: o script pode ser escrito para gerar **só as subseções aprovadas** (parâmetro) ou o bloco inteiro de cada vez, mas sempre com a v10 intacta e a v11 regravada.
- Se o usuário preferir editar à mão: gerar o texto em `.md` (por exemplo `Documento/handoff_resultados_13_3/rascunhos/5XX_<subsecao>.md`) e só depois inserir no Word quando ele aprovar.

## 4. Pontos a decidir com o usuário (perguntar, não assumir)

1. Quais subseções da lista acima ficam (principalmente a 5 e a 6) e a ordem.
2. As análises opcionais (por dobra, por instante, resíduos): fazer ou não.
3. O que fazer com o Apêndice E.11 (previsão a priori dos 4 ensaios) enquanto não há validação externa: manter como está, já que será usado depois.
4. Modo: ler no chat e editar, ou entrar direto no Word para feedback depois.
