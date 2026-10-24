# Registro de Arquivos Depreciados — Etapa 0.3 (`old/`)

Em conformidade com a **Regra 5 de Governança do Projeto LOP** (*"Nunca apague nada — Política da pasta `old/`"*), esta pasta preserva integralmente a primeira versão dos artefatos gerados na Etapa 0.3 antes da refatoração solicitada em `2026-10-22`.

## Justificativa de Arquivamento

1. **`fig_03b_whitebox_painel_eta_antigo_vs_novo.png` / `.pdf`**, **`fig_03c_whitebox_16_ensaios_grid_4x4.png` / `.pdf`** e **`fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.png` / `.pdf`**:
   - **Motivo da Substituição**: Na versão inicial, as figuras comparativas do modelo White-Box incluíam o parâmetro empírico de amortecimento cinético `α = 5500 μm/min`. Por decisão de modelagem na Etapa 0.3, as comparações do White-Box foram refeitas **sem considerar o parâmetro `α` (`α = 0`)**, permitindo avaliar o efeito físico puro da divisão da distribuição RRB por `D³` sem a interferência do amortecimento empírico.
2. **`fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.png` / `.pdf`**:
   - **Motivo da Substituição**: Os rótulos e anotações dos painéis (a), (b) e (c) foram aprimorados para explicitar de forma didática por que a curva da Etapa 0.2 (`fig_02_granulometria_RRB.png`, que plota `f_m(D)` antes de entrar na equação de conversão) coincide exatamente com a curva efetiva `D³ · f_n(D) = f_m(D)` obtida dentro da equação de conversão após dividir a RRB por `D³`.
3. **`tabela_comparativa_whitebox_antigo_vs_novo_d3.csv`** e **`relatorio_etapa_0_3_transformacao_rrb_d3.md`**:
   - **Motivo da Substituição**: Atualizados para priorizar as métricas do modelo White-Box puro sem `α` (`α = 0`).
