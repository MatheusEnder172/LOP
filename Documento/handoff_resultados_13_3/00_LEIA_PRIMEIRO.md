# Handoff: escrita dos Resultados do híbrido serial (modelo 13 + 3)

Escrito em 09/11/2026. Serve para um novo chat continuar sem depender da conversa anterior. Entrega final do relatório: **13/11/2026**.

## O que o novo chat vai fazer

Escrever, no Word, a parte de **Resultados do modelo híbrido serial** usando só o que já existe: o modelo **v2** (comitê de 10 redes), treinado em **13 ensaios** (treino e validação cruzada) e avaliado em **3 ensaios de teste cego** (7, 8 e 14). O foco é **treinamento e validação**. Os 4 ensaios novos de laboratório entram **depois**, como um extra, quando os dados forem esclarecidos (ver `04_ensaios_novos_depois.md`).

## Decisão do usuário (09/11, "bater o martelo")

- Os Resultados mostram a **individualidade de cada modelagem**. Cada membro do grupo apresenta a sua. Aqui entra **só a serial**.
- Parte da modelagem: **breve**, só o que ainda não está em Métodos nem nos Apêndices B a E.
- A maior parte do texto vai para **treinamento e validação** (13 ensaios com validação cruzada, 3 de teste cego).
- Nada de comparar com RF, SVR, XGBoost ou MCDA (decisão de 24/10). Referências usadas: fenomenológico puro e v1 (configuração de referência).
- Os 4 ensaios novos **não** entram agora. Comparação já feita (E2 e E3 possivelmente trocados; E1 e E4 acima do limite estequiométrico) está em `Código/outputs/etapa_4_3_previsao_novos_ensaios/medicoes/relatorio_comparacao_medicoes.md`. O usuário aguarda resposta do laboratório e do orientador.

## Ordem de leitura

1. Este arquivo.
2. `01_decisoes_e_regras.md` (regras permanentes, modo de trabalho).
3. `02_estado_do_documento_e_estrutura.md` (o que a v10 já tem e a estrutura proposta).
4. `03_numeros_e_fontes.md` (números, de qual CSV vêm, e o que NÃO está verificado).
5. `04_ensaios_novos_depois.md` (só para saber o que fica de fora agora).
6. Memória do projeto: `C:\Users\Usuário\.claude\projects\C--us-trem-Doc-UFMG-9-Lop\memory\MEMORY.md`.
7. DEVLOG: as entradas de 08/11 (Relatório v10) e 09/11 (medições) no topo de `Codigo_v4/DEVLOG.md`.

O prompt para abrir o novo chat está em `PROMPT_NOVO_CHAT.md` (esta pasta). **Não use** `Codigo_v4/PROMPT_NOVO_CHAT.md` nem `PLANO_RETOMADA_PROXIMO_CHAT.md` como ponto de partida: são de 07/11 e estão desatualizados (pedem Etapas 1 a 6 que já foram feitas ou mudaram).

## Onde está o quê

| O quê | Onde |
| :-- | :-- |
| Documento atual | `Codigo_v4/Documento/RELATÓRIO FINAL LOP_v10.docx` (não versionado; não alterar) |
| Scripts que geram o Word | `Codigo_v4/Documento/ferramentas/` (`docx_utils.py`, `adicionar_resultados_v10.py`; README na pasta) |
| Figuras e tabelas de apoio dos Resultados | `Codigo_v4/Código/outputs/etapa_4_4_resultados_hibrido_serial/` (`fig_rh_01..04`, 4 CSVs) |
| Script dessas figuras | `Codigo_v4/Código/etapas/etapa_4_4_resultados_hibrido_serial/analisar_resultados.py` |
| Métricas do teste cego | `Código/outputs/etapa_3_2/subetapa_3_2_6_mlp_otimizacao/fase_e/` |
| Validação cruzada (10 sementes) | `.../fase_b2/` (finalistas) e `.../fase_a/` (protocolo) |
| Perdas físicas, ajuste fino (já descartados) | `.../fase_c/`, `.../fase_d/` (Apêndice E.8 a E.10) |
| Modelo salvo (hashes) | `Código/outputs/models_saved/mlp_v2/` (`SHA256SUMS.txt`) |
| Previsões nos 16 ensaios | `Código/outputs/etapa_4_2_avaliacao_indomain/tabela_predicoes_detalhadas_16_ensaios.csv` |
| Repositório | `C:\us trem\Doc\UFMG\9\Lop\Codigo_v4`, branch `feat/mlp-otimizacao`, PR #1 |
