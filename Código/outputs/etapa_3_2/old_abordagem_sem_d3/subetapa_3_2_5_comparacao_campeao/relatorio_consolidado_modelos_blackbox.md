# Relatório Técnico Consolidado — Subetapa 3.2.5: Comparação Geral e Seleção do Modelo Campeão

## 1. Sumário Executivo e Veredito da Etapa 3.2
A Etapa 3.2 teve como objetivo central conceber, treinar, validar e comparar quatro famílias distintas de modelos orientados a dados (Data-Driven Models - DDM / Black-Box) para a predição da taxa de retração interfacial |v(t)| = dD/dt no processo de lixiviação de concentrado de zinco:
1. **Multi-Layer Perceptron (MLP em PyTorch)**: Rede neural com 3 camadas ocultas [128, 64, 32], ativação GELU suave e cabeça física estritamente não-negativa via Softplus.
2. **Random Forest Regressor (RF Regularizado)**: Conjunto de 100 árvores rasas (max_depth=6, min_samples_leaf=2) com target em escala ln(1 + |v|).
3. **Support Vector Regression (SVR RBF)**: Regressão por vetores de suporte com kernel gaussiano (C=100,0, ε=0,10, γ=0,50).
4. **XGBoost Regressor (XGB Profundo)**: Gradient Boosting regularizado com 150 árvores (max_depth=8, η=0,05, subsample 80%).

Com base na Análise de Decisão Multicritério (MCDA) que pondera **Generalização Cega (30%)**, **Robustez Espacial em CV (25%)**, **Erro Residual (20%)**, **Velocidade de Inferência (15%)** e **Suavidade Derivativa para Integração no Solver PBM (10%)**, o modelo declarado formalmente como **CAMPEÃO DA ETAPA 3.2** é:

**MODELO CAMPEÃO: RANDOM FOREST (Score MCDA: 79.50/100)**

---

## 2. Tabela Comparativa Consolidada dos Quatro Competidores

| Métrica de Avaliação | MLP (PyTorch) | Random Forest | SVR (RBF) | XGBoost | Unidade / Critério |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **R² Teste Cego (Global)** | **0.8297** | **0.9120** | **0.6031** | **0.8009** | Maior é melhor (≥ 0,80) |
| **RMSE Teste Cego** | 26.88 | 19.33 | 41.04 | 29.06 | µm/min (Menor é melhor) |
| **MAE Teste Cego** | 5.06 | 5.15 | 8.16 | 6.76 | µm/min (Menor é melhor) |
| **R² Validação Cruzada (CV)** | 0.2560 | 0.7136 | 0.0743 | 0.6503 | Média nas 4 dobras |
| **R² Treino (13 ensaios)** | 0.9987 | 0.8368 | 0.1473 | 0.8325 | Capacidade de ajuste |
| **Violação Física (|v| < 0)** | **0,00%** | **0,00%** | **0,00%** | **0,00%** | Inegociável (0,00%) |
| **Latência por Ponto** | 262.0 µs | 19685.1 µs | 105.2 µs | 233.4 µs | Tempo de cálculo unitário |
| **Latência Lote (1000 pontos)** | 0.33 ms | 21.05 ms | 5.94 ms | 1.68 ms | Tempo de inferência vetorizada |
| **Score Final MCDA (0-100)** | **67.16** | **79.50** | **20.94** | **71.30** | **Ranking ponderado** |

---

## 3. Desempenho nos Três Ensaios de Teste Cego

Os três ensaios mantidos estritamente intocados representam regimes operacionais distintos:
* **Ensaio 8**: Estequiométrico neutro (C_A0 = 0,50 mol/L, η = 1,0);
* **Ensaio 14**: Leve excesso de ácido (C_A0 = 1,00 mol/L, η = 1,5);
* **Ensaio 7**: Forte excesso de ácido (C_A0 = 0,50 mol/L, η = 3,1).

| Ensaio | Regime Cinético | MLP (R²) | Random Forest (R²) | SVR (R²) | XGBoost (R²) | Destaque do Ensaio |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **8** | Estequiométrico Neutro | 0,8105 | 0,9496 | 0,3843 | **0,9801** | XGBoost obtém o recorde de precisão |
| **14** | Leve Excesso Ácido | 0,9163 | 0,9168 | **0,9692** | 0,6350 | SVR atinge a melhor aderência assintótica |
| **7** | Forte Excesso Ácido | 0,8165 | **0,8824** | 0,5287 | 0,7759 | Random Forest demonstra maior robustez |

---

## 4. Análise Crítica dos Trade-offs e Justificativa do Campeão

### 4.1. Por que o Random Forest venceu a seleção?
1. **Consistência em Múltiplos Regimes**: O Random Forest manteve R² > 0,88 em todos os ensaios de teste cego, enquanto concorrentes oscilaram dependendo do regime estequiométrico.
2. **Robustez Espacial**: Na validação cruzada por ensaios (GroupKFold), obteve **R² = 0.7136**, provando que não sofre de memorização espúria.
3. **Conservação Termodinâmica**: Violação física nula (0,00%) graças à projeção em escala logarítmica ln(1 + |v|).
4. **Desempenho no Teste Cego**: Erro quadrático médio de apenas **19.33 µm/min**, o menor entre todos os quatro competidores.

### 4.2. Estratégia de Transição para a Etapa 4 (Acoplamento Híbrido Serial)
Na Etapa 4, o modelo campeão será acoplado diretamente ao **Balanço Populacional Multicomponente (PBM)**:
∂n(D, t)/∂t + ∂[v(t; x) · n(D, t)]/∂D = 0
Onde v(t; x) é suprido em tempo real pelo Random Forest, alimentando as equações de Herbst para o consumo ácido e a evolução da distribuição granulométrica q₃(D, t).

---

## 5. Figuras Científicas de Validação Geradas (300 DPI)
* `fig_11a_comparativo_global_metricas.png` e `.pdf`: Barras comparativas de R², RMSE e MAE entre Treino, CV e Teste Cego.
* `fig_11b_paridade_consolidada_4_modelos.png` e `_log.png`: Painéis 2x2 de paridade 1:1 linear e log-log cobrindo 5 ordens de magnitude.
* `fig_11c_trajetorias_comparativas_teste.png` e `_log.png`: Sobreposição das trajetórias temporais preditas vs. dados reais nos ensaios 8, 14 e 7.
* `fig_11d_distribuicao_residuos_boxplots.png` e `.pdf`: Boxplots de dispersão de erro absoluto e densidade probabilística de resíduos.
* `fig_11e_radar_selecao_campeao.png` e `.pdf`: Gráfico polar (radar) ilustrando o perfil multidimensional dos 4 competidores.
