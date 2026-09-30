# Relatório de Validação Técnica — Subetapa 3.2.2: Random Forest Regressor

## 1. Sumário Executivo
Nesta subetapa, implementou-se o modelo de conjunto por árvores de decisão **KineticsRandomForest** para a predição contínua da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições do reator $[T, C_{A0}, η, t]$.

Investigaram-se cinco configurações de hiperparâmetros sob o mesmo protocolo de **GroupKFold (4 dobras disjuntas por ensaio)**:
1. **RF-Baseline (Default)**: `n_estimators=100`, profundidade ilimitada.
2. **RF-Regularizado (Shallow)**: `n_estimators=100`, `max_depth=6`, `min_samples_leaf=2`.
3. **RF-Profundo (Deep Ensemble)**: `n_estimators=200`, `max_depth=12`.
4. **RF-Robusto (Campeão)**: `n_estimators=300`, `max_depth=10`, `min_samples_split=4`, `min_samples_leaf=2`.
5. **RF-LinearTarget (Sem Log1p)**: Treinado em escala linear direta para evidenciar a necessidade de compressão logarítmica.

A configuração campeã foi a **RF-Regularizado (Shallow)**, alcançando **$R^2 = 0.8368$ no Treino** e **$R^2 = 0.9120$ no Teste Cego**.

---

## 2. Comparativo de Hiperparâmetros na Validação Cruzada (4 Dobras Disjuntas)

| Configuração | Estimadores | Max Depth | Min Split | Min Leaf | Target | $R^2$ Médio (CV) | RMSE (µm/min) | MAE (µm/min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RF-Baseline (Default)** | 100 | None | 2 | 1 | `log1p` | **0.6676 ± 0.1056** | 51.33 | 9.39 |
| **RF-Regularizado (Shallow)** | 100 | 6 | 5 | 2 | `log1p` | **0.7136 ± 0.1227** | 48.09 | 8.65 |
| **RF-Profundo (Deep Ensemble)** | 200 | 12 | 2 | 1 | `log1p` | **0.6505 ± 0.1048** | 52.31 | 9.45 |
| **RF-Robusto (Campeão)** | 300 | 10 | 4 | 2 | `log1p` | **0.7094 ± 0.1301** | 48.62 | 8.83 |
| **RF-LinearTarget (Sem Log1p)** | 100 | 10 | 4 | 2 | `linear` | **0.6587 ± 0.1082** | 50.90 | 9.23 |

---

## 3. Desempenho Global do Modelo Campeão (RF-Regularizado (Shallow))

* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * $R^2$: **0.8368**
  * RMSE: **37.59 µm/min**
  * MAE: **5.13 µm/min**
  * Erro Máximo: **626.84 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras intocadas: Ens 8, 14 e 7)**:
  * $R^2$: **0.9120**
  * RMSE: **19.33 µm/min**
  * MAE: **5.15 µm/min**
  * Erro Máximo: **191.04 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (restrição termodinâmica garantida estritamente).

---

## 4. Avaliação Individual nos Ensaios de Teste Cego

| Ensaio | Regime Físico-Químico | $C_{A0}$ (mol/L) | η (-) | $R^2$ Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **7** | Forte Excesso Ácido | 0.50 | 3.1 | **0.8824** | 25.55 | 8.63 |
| **8** | Estequiométrico Neutro | 0.50 | 1.0 | **0.9496** | 13.82 | 2.85 |
| **14** | Leve Excesso Ácido | 1.00 | 1.5 | **0.9168** | 16.64 | 3.96 |

---

## 5. Importância dos Atributos Físicos (Interpretabilidade)

| Atributo | Significado Físico-Químico | Importância MDI (Gini) | Importância por Permutação (Teste) |
| :--- | :--- | :---: | :---: |
| `t_min` | Tempo de reação (decaimento cinético) | **69.5%** | **ΔR² = 1.9503 ± 0.1291** |
| `razao_molar_eta` | Razão estequiométrica (disponibilidade ácida) | **18.6%** | **ΔR² = -0.0009 ± 0.0418** |
| `CA0_mol_L` | Força motriz de concentração ácida | **11.9%** | **ΔR² = -0.0009 ± 0.0134** |
| `temperatura_C` | Temperatura do banho (invariante na bancada) | **0.0%** | **ΔR² = -0.0000 ± 0.0000** |

---

## 6. Figuras de Diagnóstico Geradas (300 DPI)
* `fig_08a_importancia_features_rf.png`: Importância de atributos MDI (Gini) e Permutação no teste cego.
* `fig_08b_predicoes_v_rf.png`: Trajetórias temporais de $|v(t)|$ preditas pelo Random Forest vs. alvos exatos nos 16 ensaios.
* `fig_08c_paridade_e_residuos_rf.png`: Gráfico de paridade 1:1 e distribuição estatística de resíduos.
* `fig_08d_comparativo_hiperparametros_rf.png`: Comparação quantitativa das configurações de hiperparâmetros na validação cruzada.
