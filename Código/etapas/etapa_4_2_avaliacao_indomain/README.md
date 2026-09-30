# Subetapa 4.2: Simulação Completa In-Domain e Benchmark Triplo (16 Ensaios de Bancada)

Este diretório contém os scripts de simulação, testes unitários automatizados e documentação técnica da **Subetapa 4.2**, correspondente à validação in-domain abrangente de conversão mássica de zinco X_Zn(t) e concentração de ácido livre C_Af(t) em todos os 16 ensaios de lixiviação de bancada de Bortot Coelho (2017).

---

## 1. Estrutura do Diretório

```
etapa_4_2_avaliacao_indomain/
├── README.md                      # Este documento de referência e guia técnico
├── avaliar_hibrido_indomain.py    # Pipeline de simulação in-domain, benchmark triplo e geração de figuras/tabelas
└── test_avaliacao_indomain.py     # Suíte de 6 testes unitários automatizados (100% aprovados)
```

---

## 2. Modelos Avaliados no Benchmark

1. **FPM Puro Baseline (Mecanicista Tradicional)**: Modelo analítico Shrinking Core com coeficiente empírico de amortecimento constante alpha = 3,43 um/min (Etapa 1.3).
2. **DDM Puro (Black-Box em Malha Aberta)**: Integração aberta da taxa interfacial do Random Forest sem conexão com o balanço de massa do solvente (Herbst) ou teto estequiométrico.
3. **Híbrido Serial Campeão (Random Forest → PBM)**: Acoplamento serial com o resolvedor do Balanço Populacional em batelada e imposição rigorosa de conservação de massa (X_Zn <= min(1, eta) e CAf >= 0).
4. **Híbridos Alternativos**: Avaliação de sensibilidade executando também MLP → PBM, XGBoost → PBM e SVR → PBM.

---

## 3. Síntese Quantitativa dos Resultados

### 3.1 Benchmark Global e por Partição de Dados
| Modelo | Partição | R² (-) | RMSE (-) | MAE (-) | Erro Máximo (-) | Redução RMSE vs. FPM |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **FPM Puro Baseline** | **Global (16 ensaios)** | 0,9030 | 0,1010 | 0,0699 | 0,3815 | — |
| **DDM Puro (sem Herbst)** | **Global (16 ensaios)** | 0,7659 | 0,1569 | 0,0987 | 0,3854 | -55,3% (Degradação) |
| **Híbrido Serial Campeão (RF)** | **Global (16 ensaios)** | **0,9737** | **0,0526** | **0,0338** | **0,1832** | **+47,9%** |
| FPM Puro Baseline | Treino (13 ensaios) | 0,8877 | 0,1081 | 0,0756 | 0,3815 | — |
| DDM Puro (sem Herbst) | Treino (13 ensaios) | 0,7117 | 0,1732 | 0,1158 | 0,3854 | -60,2% |
| **Híbrido Serial Campeão (RF)** | **Treino (13 ensaios)** | **0,9699** | **0,0560** | **0,0360** | **0,1832** | **+48,2%** |
| FPM Puro Baseline | Teste Cego (3 ensaios) | 0,9616 | 0,0609 | 0,0449 | 0,1473 | — |
| DDM Puro (sem Herbst) | Teste Cego (3 ensaios) | 0,9880 | 0,0341 | 0,0243 | 0,0867 | +44,0% |
| **Híbrido Serial Campeão (RF)** | **Teste Cego (3 ensaios)** | **0,9880** | **0,0341** | **0,0243** | **0,0867** | **+44,0%** |

### 3.2 Comparativo dos 4 Preditores Híbridos (Conversão X_Zn)
| Modelo Híbrido | R² Global | RMSE Global | R² Teste Cego | RMSE Teste Cego | Diagnóstico |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Híbrido Serial (RF Campeão)** | **0,9737** | **0,0526** | **0,9880** | **0,0341** | **CAMPEÃO GERAL (Robusto, sem sobre-ajuste)** |
| **Híbrido Serial (MLP)** | **0,9828** | **0,0425** | **0,9891** | **0,0324** | Excelente acurácia, próximo ao RF |
| **Híbrido Serial (XGBoost)** | 0,9339 | 0,0833 | 0,9293 | 0,0827 | Discretização em degraus reduz acurácia pontual |
| **Híbrido Serial (SVR)** | 0,0438 | 0,3170 | 0,8179 | 0,1328 | Acúmulo de erro na integração do pulso inicial |

---

## 4. Artefatos Científicos Produzidos

Os artefatos encontram-se salvos em [`Código/outputs/etapa_4_2_avaliacao_indomain/`](../../outputs/etapa_4_2_avaliacao_indomain/):
1. **Figuras Científicas (300 DPI — PNG + PDF Vetorial)**:
   - `fig_12a_reconstrucao_XZn_hibrido_16_ensaios.png` e `.pdf` (Painel 4x4 com os 16 ensaios);
   - `fig_12a_reconstrucao_XZn_hibrido_16_ensaios_log.png` e `.pdf` (Escala semilogarítmica em 1 - X_Zn);
   - `fig_12b_paridade_XZn_3modelos.png` e `.pdf` (Paridade 1:1 com faixas de +/- 5% e +/- 10%);
   - `fig_12c_comparativo_global_XZn_barras.png` e `.pdf` (Gráficos de barras de R² e RMSE);
   - `fig_12d_heatmap_ganho_relativo_hibrido.png` e `.pdf` (Heatmap 4x4 de ganho Delta R² e redução de RMSE).
2. **Tabelas de Dados em Formato CSV**:
   - `tabela_predicoes_detalhadas_16_ensaios.csv` (128 observações pareadas);
   - `tabela_metricas_indomain_hibrido_vs_fpm.csv` (Métricas ensaio a ensaio);
   - `tabela_comparativo_quatro_hibridos_XZn.csv` (Métricas por partição e modelo).
3. **Relatórios Técnicos**:
   - `relatorio_etapa_4_2_hibrido_indomain.md` (Sumário executivo de resultados);
   - `fundamentacao_acoplamento_hibrido_LOP.md` (Documento conceitual completo).
