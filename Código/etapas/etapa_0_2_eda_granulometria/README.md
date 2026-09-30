# Etapa 0.2: Visualização e Validação da Distribuição Granulométrica (RRB)

## Objetivo
Avaliar quantitativa e visualmente a distribuição de tamanhos das partículas do concentrado ustulado de zinco (calcina da Nexa Resources - Três Marias), comparando os dados experimentais combinados de peneiramento a úmido e difração a laser com o modelo analítico de Rosin-Rammler-Bennet (RRB).

## Script de Geração
- [`visualizar_granulometria_rrb.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/etapas/etapa_0_2_eda_granulometria/visualizar_granulometria_rrb.py)

## Entregas e Documentação Técnica (Outputs)
Os resultados gerados estão centralizados em [`Código/outputs/etapa_0_2/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_0_2/):
- **Discussão analítica e métricas estatísticas**: [`resumo_observacoes_etapa_0_2.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_0_2/resumo_observacoes_etapa_0_2.md)
  - Formulação analítica da função acumulada $F(D)$ e da função densidade $f_0(D)$.
  - Linearização clássica do modelo RRB: $\ln[\ln[1/(1-F)]] = m \ln(D) - m \ln(D_{63,2})$.
  - Confirmação dos parâmetros ajustados: $D_{63,2} = 41,65\,\mu\text{m}$, $m = 1,022$ e diâmetro médio $\bar{\mu} = 41,28\,\mu\text{m}$.
  - Métricas estatísticas de aderência ($R^2$, RMSE, MAE).
- **Gráficos em alta resolução (300 DPI e Vetorial)**:
  - [`fig_02_granulometria_RRB.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_0_2/fig_02_granulometria_RRB.png)
  - [`fig_02_granulometria_RRB.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_0_2/fig_02_granulometria_RRB.pdf)
