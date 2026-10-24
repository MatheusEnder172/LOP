# Relatório de Validação Técnica — Subetapa 3.2.2: Random Forest Regressor

## 1. Sumário Executivo
Nesta subetapa, implementou-se o modelo de conjunto por árvores de decisão **KineticsRandomForest** para a predição contínua da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições do reator $[T, C_{A0}, η, t]$.

Investigaram-se cinco configurações de hiperparâmetros sob o mesmo protocolo de **GroupKFold (4 dobras disjuntas por ensaio)**:
1. **RF-Baseline (Default)**: `n_estimators=100`, profundidade ilimitada.
2. **RF-Regularizado (Shallow)**: `n_estimators=100`, `max_depth=6`, `min_samples_leaf=2`.
3. **RF-Profundo (Deep Ensemble)**: `n_estimators=200`, `max_depth=12`.
4. **RF-Robusto (Campeão)**: `n_estimators=300`, `max_depth=10`, `min_samples_split=4`, `min_samples_leaf=2`.
5. **RF-LinearTarget (Sem Log1p)**: Treinado em escala linear direta para evidenciar a necessidade de compressão logarítmica.

A configuração campeã foi a **RF-Profundo (Deep Ensemble)**, alcançando **$R^2 = 0.9900$ no Treino** e **$R^2 = 0.9539$ no Teste Cego**.

---

## 2. Comparativo de Hiperparâmetros na Validação Cruzada (4 Dobras Disjuntas)

| Configuração | Estimadores | Max Depth | Min Split | Min Leaf | Target | $R^2$ Médio (CV) | RMSE (µm/min) | MAE (µm/min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RF-Baseline (Default)** | 100 | None | 2 | 1 | `log1p` | **0.8377 ± 0.0997** | 3.32 | 1.30 |
| **RF-Regularizado (Shallow)** | 100 | 6 | 5 | 2 | `log1p` | **0.7715 ± 0.1191** | 4.01 | 1.42 |
| **RF-Profundo (Deep Ensemble)** | 200 | 12 | 2 | 1 | `log1p` | **0.8415 ± 0.0957** | 3.29 | 1.29 |
| **RF-Robusto (Campeão)** | 300 | 10 | 4 | 2 | `log1p` | **0.7852 ± 0.1216** | 3.88 | 1.39 |
| **RF-LinearTarget (Sem Log1p)** | 100 | 10 | 4 | 2 | `linear` | **0.8142 ± 0.1101** | 3.60 | 1.41 |

---

## 3. Desempenho Global do Modelo Campeão (RF-Profundo (Deep Ensemble))

* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * $R^2$: **0.9900**
  * RMSE: **0.87 µm/min**
  * MAE: **0.15 µm/min**
  * Erro Máximo: **11.79 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras intocadas: Ens 8, 14 e 7)**:
  * $R^2$: **0.9539**
  * RMSE: **1.83 µm/min**
  * MAE: **0.95 µm/min**
  * Erro Máximo: **11.36 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (restrição termodinâmica garantida estritamente).

---

## 4. Avaliação Individual nos Ensaios de Teste Cego

| Ensaio | Regime Físico-Químico | $C_{A0}$ (mol/L) | η (-) | $R^2$ Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **7** | Forte Excesso Ácido | 0.50 | 3.1 | **0.9059** | 2.66 | 2.29 |
| **8** | Estequiométrico Neutro | 0.50 | 1.0 | **0.9266** | 1.49 | 0.27 |
| **14** | Leve Excesso Ácido | 1.00 | 1.5 | **0.9920** | 0.87 | 0.29 |

---

## 5. Importância dos Atributos Físicos (Interpretabilidade)

| Atributo | Significado Físico-Químico | Importância MDI (Gini) | Importância por Permutação (Teste) |
| :--- | :--- | :---: | :---: |
| `t_min` | Tempo de reação (decaimento cinético) | **59.9%** | **ΔR² = 1.7667 ± 0.2499** |
| `razao_molar_eta` | Razão estequiométrica (disponibilidade ácida) | **27.3%** | **ΔR² = 0.4797 ± 0.0736** |
| `CA0_mol_L` | Força motriz de concentração ácida | **12.8%** | **ΔR² = 0.1102 ± 0.0693** |

---

## 6. Figuras de Diagnóstico Geradas (300 DPI)
* `fig_08a_importancia_features_rf.png`: Importância de atributos MDI (Gini) e Permutação no teste cego.
* `fig_08b_predicoes_v_rf.png`: Trajetórias temporais de $|v(t)|$ preditas pelo Random Forest vs. alvos exatos nos 16 ensaios.
* `fig_08c_paridade_e_residuos_rf.png`: Gráfico de paridade 1:1 e distribuição estatística de resíduos.
* `fig_08d_comparativo_hiperparametros_rf.png`: Comparação quantitativa das configurações de hiperparâmetros na validação cruzada.
