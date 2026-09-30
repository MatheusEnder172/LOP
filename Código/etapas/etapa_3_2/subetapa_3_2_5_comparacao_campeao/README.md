# Subetapa 3.2.5: Comparação Consolidada e Seleção do Modelo Campeão

**Projeto**: Modelagem Híbrida de Lixiviação de Zinco (DEQ/UFMG)  
**Etapa Superior**: Etapa 3.2 — Modelagem Black-Box (DDM Puro)  
**Responsável**: Antigravity AI Pair Programmer & Equipe LOP  
**Data**: 26 de Setembro de 2026  

---

## 1. Objetivo da Subetapa 3.2.5

Conduzir a avaliação comparativa sistemática, dimensional, estatística e computacional entre os quatro modelos orientados por dados (*Data-Driven Models* - DDM / Black-Box) desenvolvidos para a predição da taxa de retração interfacial |v(t)| = dD/dt:
1. **Multi-Layer Perceptron (MLP em PyTorch)** — Rede neural profunda com camadas LayerNorm, ativação suave GELU e projeção não-negativa Softplus;
2. **Random Forest Regressor (RF Regularizado)** — Ensemble paralelo de 100 árvores rasas com target em espaço logarítmico;
3. **Support Vector Regression (SVR RBF)** — Regressão com kernel gaussiano e margem de tolerância ε;
4. **XGBoost Regressor (XGB Profundo)** — Extreme Gradient Boosting com regularização L1/L2 e expansão de Newton de 2ª ordem.

A comparação culmina na aplicação da **Matriz de Decisão Multicritério (MCDA)** para a seleção objetiva e formal do **Modelo Campeão da Etapa 3.2**, o qual será acoplado diretamente ao Balanço Populacional Multicomponente (PBM) na **Etapa 4 (Acoplamento Híbrido Serial)**.

---

## 2. Tabela de Desempenho Consolidado dos Quatro Competidores

| Métrica de Avaliação | MLP (PyTorch) | Random Forest | SVR (RBF) | XGBoost | Unidade / Critério |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **R² Teste Cego (Global)** | 0,8297 | **0,9120** | 0,6031 | 0,8009 | Maior é melhor (≥ 0,80) |
| **RMSE Teste Cego** | 26,88 | **19,33** | 41,04 | 29,06 | µm/min (Menor é melhor) |
| **MAE Teste Cego** | 5,06 | **5,15** | 8,16 | 6,76 | µm/min (Menor é melhor) |
| **R² Validação Cruzada (CV)** | 0,2560 ± 0,1702 | **0,7136 ± 0,1227** | 0,0743 ± 0,0666 | 0,6503 ± 0,2176 | Média nas 4 dobras |
| **R² Treino (13 ensaios)** | 0,9987 | 0,8368 | 0,1473 | 0,8325 | Capacidade de ajuste |
| **Violação Física (|v| < 0)** | **0,00%** | **0,00%** | **0,00%** | **0,00%** | Inegociável (0,00%) |
| **Latência por Ponto** | 262,0 µs | 19685,1 µs | **105,2 µs** | 233,4 µs | Tempo unitário de cálculo |
| **Latência Lote (1000 pontos)** | **0,33 ms** | 21,05 ms | 5,94 ms | 1,68 ms | Inferência vetorizada |
| **Score Final MCDA (0-100)** | 67,16 | **79,50** | 20,94 | 71,30 | **Ranking ponderado** |

---

## 3. Desempenho nos Três Ensaios de Teste Cego

Os três ensaios mantidos estritamente intocados durante a calibração representam vértices operacionais distintos da matriz experimental de Herbst:
* **Ensaio 8**: Estequiométrico neutro (C_A0 = 0,50 mol/L, η = 1,0);
* **Ensaio 14**: Leve excesso de ácido (C_A0 = 1,00 mol/L, η = 1,5);
* **Ensaio 7**: Forte excesso de ácido (C_A0 = 0,50 mol/L, η = 3,1).

| Ensaio | Regime Cinético | MLP (R²) | Random Forest (R²) | SVR (R²) | XGBoost (R²) | Destaque do Ensaio |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **8** | Estequiométrico Neutro | 0,8290 | 0,9496 | 0,3843 | **0,9801** | XGBoost atinge o recorde de precisão do projeto |
| **14** | Leve Excesso Ácido | **0,9712** | 0,9168 | 0,9692 | 0,6350 | MLP e SVR alcançam excelente curvatura contínua |
| **7** | Forte Excesso Ácido | 0,7436 | **0,8824** | 0,5287 | 0,7759 | Random Forest demonstra superior estabilidade |

---

## 4. Análise de Decisão Multicritério (MCDA) e Modelo Campeão

O cálculo do score de cada modelo ponderou 5 dimensões quantitativas:
* **Generalização em Teste Cego (Peso 30%)**: Capacidade de prever ensaios intocados;
* **Robustez Espacial em CV (Peso 25%)**: Estabilidade frente a rotações do GroupKFold;
* **Precisão Residual (Peso 20%)**: Inverso do erro quadrático médio (1 / RMSE);
* **Velocidade de Inferência (Peso 15%)**: Throughput e latência em lote de 1000 pontos;
* **Suavidade Derivativa para PBM (Peso 10%)**: Classe de diferenciabilidade C^∞ vs C⁰.

### Resultado Formal do Ranking:
1. **1º Lugar (CAMPEÃO): Random Forest Regressor — Score: 79,50 / 100**
2. **2º Lugar (Vice-Campeão): XGBoost Regressor — Score: 71,30 / 100**
3. **3º Lugar: Multi-Layer Perceptron (PyTorch) — Score: 67,16 / 100**
4. **4º Lugar: Support Vector Regression (SVR) — Score: 20,94 / 100**

---

## 5. Estrutura de Arquivos da Subetapa

```
subetapa_3_2_5_comparacao_campeao/
├── README.md                                # Este documento descritivo
├── comparar_modelos.py                      # Pipeline completo de benchmark, MCDA e gráficos
└── test_comparativo.py                      # Suíte de testes unitários (100% aprovada)
```

### Arquivos Gerados em `Código/outputs/etapa_3_2/subetapa_3_2_5_comparacao_campeao/`:
* `tabela_consolidada_modelos_blackbox.csv`: Métricas globais consolidadas dos 4 modelos;
* `tabela_comparativa_ensaios_teste.csv`: Desempenho nos ensaios 8, 14 e 7;
* `tabela_todos_16_ensaios_4_modelos.csv`: Resultados para todos os 16 ensaios;
* `tabela_ranking_multicriterio_mcda.csv`: Matriz detalhada de pontuação e ranking;
* `relatorio_consolidado_modelos_blackbox.md`: Relatório técnico de consolidação;
* `fundamentacao_comparacao_e_selecao_campeao_LOP.md`: Guia didático-científico exaustivo;
* `fig_11a_comparativo_global_metricas.png` e `.pdf`: Barras comparativas de métricas;
* `fig_11b_paridade_consolidada_4_modelos.png` e `_log.png` (+ `.pdf`): Painéis 2x2 de paridade;
* `fig_11c_trajetorias_comparativas_teste.png` e `_log.png` (+ `.pdf`): Trajetórias temporais sobrepostas;
* `fig_11d_distribuicao_residuos_boxplots.png` e `.pdf`: Boxplots e densidade de resíduos;
* `fig_11e_radar_selecao_campeao.png` e `.pdf`: Gráfico radar multidimensional.

### Metadados do Campeão para a Etapa 4:
* `Código/outputs/models_saved/modelo_campeao_info.json`: Arquivo com apontamento formal para `random_forest/rf_kinetics_v1.joblib` e metadados de carregamento para a modelagem híbrida serial.

---

## 6. Como Executar

```bash
# Executar a rotina completa de comparação e geração de gráficos
python Código/etapas/etapa_3_2/subetapa_3_2_5_comparacao_campeao/comparar_modelos.py

# Executar a suíte de testes unitários
python -m pytest Código/etapas/etapa_3_2/subetapa_3_2_5_comparacao_campeao/test_comparativo.py -v
```
