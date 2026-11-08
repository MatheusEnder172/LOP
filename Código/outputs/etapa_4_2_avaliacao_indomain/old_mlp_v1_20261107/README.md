# Registro de Arquivos Depreciados — Etapa 4.2 (instantâneo antes da linha da MLP v2)

## 1. Arquivos depreciados
Todas as saídas da Etapa 4.2 que o script `avaliar_hibrido_indomain.py` regenera (17 arquivos):
- tabelas: `tabela_predicoes_detalhadas_16_ensaios.csv`, `tabela_metricas_indomain_hibrido_vs_fpm.csv`, `tabela_comparativo_quatro_hibridos_XZn.csv`;
- relatórios: `relatorio_etapa_4_2_hibrido_indomain.md`, `fundamentacao_acoplamento_hibrido_LOP.md`;
- figuras (PNG e PDF): `fig_12a_*` (3 versões), `fig_12b_paridade_XZn_3modelos`, `fig_12c_comparativo_global_XZn_barras`, `fig_12d_heatmap_ganho_relativo_hibrido`.

`fig_comparativo_escalas_cinetica_hibrido.*` não é gerada por esse script e foi mantida na pasta principal.

## 2. Data e motivo
- **Data**: 07/11/2026.
- **Motivo**: integração da MLP v2 (comitê de 10 redes da Subetapa 3.2.6) à Etapa 4.2. O script passou a acrescentar a linha "Híbrido Serial (MLP v2, comitê)" às tabelas, ao relatório e à Figura 12c; as demais linhas não mudam. O instantâneo guarda o estado em que a linha da v1 (MLP Campeão) tem RMSE global de 0,0257, para comparação e reprodutibilidade.

## 3. Novos arquivos em substituição
Os mesmos nomes em `Código/outputs/etapa_4_2_avaliacao_indomain/`. Conferência feita na regeneração: todas as colunas e linhas anteriores coincidem com este instantâneo (diferença máxima de 2,2e-16 nas predições; 0 nas métricas); só foram acrescentadas colunas `*_v2*` e as linhas da v2.
