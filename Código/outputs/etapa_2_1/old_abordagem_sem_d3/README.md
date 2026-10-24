# Preservação Histórica — Gráficos e Relatórios da Etapa 2.1 (Abordagem Antiga sem Divisão por D³)

## 1. Contexto e Motivação
Este diretório preserva integralmente as figuras, métricas e relatórios técnicos da Etapa 2.1 gerados com a distribuição mássica direta da dissertação de Fabrício Bortot Coelho (2017), em estrito cumprimento à **Regra 5 de Governança** (*"Nunca apague nada — Política da pasta old/"*).

## 2. Conteúdo Preservado
- `fig_04_reconstrucao_XZn_vs_experimento.png` e `.pdf`: Painel 2×2 da conversão reconstruída vs. dados experimentais.
- `fig_04_reconstrucao_XZn_vs_experimento_log.png` e `.pdf`: Versão em escala logarítmica.
- `fig_05_curvas_v_otimizadas.png` e `.pdf`: Curvas ótimas de retração interfacial `v(t)` com escala de até `-650 µm/min`.
- `fig_05_curvas_v_otimizadas_log.png` e `.pdf`: Versão logarítmica das curvas `v(t)`.
- `fig_06_comparacao_malha_experimental_vs_densa.png` e `.pdf`: Comparativo de densidade amostral (128 vs. 976 pontos).
- `tabela_metricas_otimizacao_inversa.csv`: Parâmetros e métricas de aderência por ensaio.
- `relatorio_validacao_etapa_2_1.md`: Relatório técnico original da validação da Opção B.
- `nota_conceitual_problema_inverso.md`: Fundamentação teórica da inversão parametrizada.

## 3. Comparação com a Nova Abordagem (RRB ÷ D³)
Na nova abordagem presente no diretório pai:
1. O diâmetro médio recuperado no `BatchPBMSolver` passa de 146,9 µm para 41,6 µm;
2. A retração necessária `δ₅₀%` diminui de 26,31 µm para 4,83 µm;
3. As taxas de retração `v(t)` passam a refletir grandezas físicas reais (~5,4 vezes menores), mantendo a qualidade de reconstrução com `r² > 0,99`.
