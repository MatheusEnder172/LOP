# Relatório de Validação Técnica — Subetapa 3.2.4: XGBoost Gradient Boosting

## 1. Sumário Executivo
Nesta subetapa, implementou-se o modelo de aprendizado por árvores de decisão impulsionadas por gradiente **KineticsXGBoost** para a predição contínua da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições operacionais $[T, C_{A0}, η, t]$.

Investigaram-se cinco configurações sob o mesmo protocolo de **GroupKFold (4 dobras disjuntas por ensaio)**:
1. **XGB-Baseline (Default)**: `n_estimators=100`, `learning_rate=0.10`, `max_depth=6`.
2. **XGB-Regularizado (Shallow)**: `n_estimators=100`, `learning_rate=0.05`, `max_depth=4`, `subsample=0.80`.
3. **XGB-Profundo (Deep)**: `n_estimators=150`, `learning_rate=0.05`, `max_depth=8`.
4. **XGB-Otimizado (Campeão)**: `n_estimators=120`, `learning_rate=0.05`, `max_depth=5`, `subsample=0.85`, `colsample=0.85`.
5. **XGB-LinearTarget (Sem Log1p)**: Treinado em escala linear direta para evidenciar a necessidade de compressão logarítmica.

A configuração campeã foi a **XGB-Profundo (Deep)**, alcançando **$R^2 = 0.8325$ no Treino** e **$R^2 = 0.8009$ no Teste Cego**.

---

## 2. Comparativo de Hiperparâmetros na Validação Cruzada (4 Dobras Disjuntas)

| Configuração | Estimadores | Taxa (η) | Max Depth | Subsample | Colsample | Target | $R^2$ Médio (CV) | RMSE (µm/min) | MAE (µm/min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGB-Baseline (Default)** | 100 | 0.1 | 6 | 1.0 | 1.0 | `log1p` | **0.5235 ± 0.2370** | 57.42 | 9.95 |
| **XGB-Regularizado (Shallow)** | 100 | 0.05 | 4 | 0.8 | 0.8 | `log1p` | **0.6268 ± 0.1676** | 55.44 | 9.28 |
| **XGB-Profundo (Deep)** | 150 | 0.05 | 8 | 0.8 | 0.8 | `log1p` | **0.6503 ± 0.2176** | 52.13 | 9.40 |
| **XGB-Otimizado (Campeão)** | 120 | 0.05 | 5 | 0.85 | 0.85 | `log1p` | **0.6475 ± 0.1714** | 53.40 | 9.27 |
| **XGB-LinearTarget (Sem Log1p)** | 100 | 0.05 | 5 | 0.85 | 0.85 | `linear` | **0.6846 ± 0.0793** | 49.64 | 10.54 |

---

## 3. Desempenho Global do Modelo Campeão (XGB-Profundo (Deep))

* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * $R^2$: **0.8325**
  * RMSE: **38.09 µm/min**
  * MAE: **4.82 µm/min**
  * Erro Máximo: **553.32 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras intocadas: Ens 8, 14 e 7)**:
  * $R^2$: **0.8009**
  * RMSE: **29.06 µm/min**
  * MAE: **6.76 µm/min**
  * Erro Máximo: **269.93 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (restrição termodinâmica garantida estritamente).

---

## 4. Avaliação Individual nos Ensaios de Teste Cego

| Ensaio | Regime Físico-Químico | $C_{A0}$ (mol/L) | η (-) | $R^2$ Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **7** | Forte Excesso Ácido | 0.50 | 3.1 | **0.7759** | 35.27 | 12.11 |
| **8** | Estequiométrico Neutro | 0.50 | 1.0 | **0.9801** | 8.69 | 1.87 |
| **14** | Leve Excesso Ácido | 1.00 | 1.5 | **0.6350** | 34.85 | 6.30 |

---

## 5. Importância dos Atributos Físicos (Ganho de Informação e Permutação)

| Atributo | Significado Físico-Químico | Importância por Ganho (Gain) | Importância por Permutação (Teste Cego) |
| :--- | :--- | :---: | :---: |
| `t_min` | Tempo de reação (decaimento cinético rápido) | **45.1%** | **ΔR² = 2.0642 ± 0.3716** |
| `razao_molar_eta` | Razão estequiométrica (potencial termodinâmico) | **33.9%** | **ΔR² = -0.0576 ± 0.0500** |
| `CA0_mol_L` | Força motriz de concentração ácida | **21.0%** | **ΔR² = -0.0820 ± 0.0556** |
| `temperatura_C` | Temperatura do banho (invariante na bancada) | **0.0%** | **ΔR² = 0.0000 ± 0.0000** |

---

## 6. Figuras de Diagnóstico Geradas (300 DPI)
* `fig_10a_importancia_features_xgb.png`: Importância de atributos por Ganho e Permutação no teste cego.
* `fig_10b_predicoes_v_xgb.png`: Trajetórias temporais de $|v(t)|$ em escala linear nos 16 ensaios.
* `fig_10b_predicoes_v_xgb_log.png`: Trajetórias temporais de $|v(t)|$ em escala semilogarítmica nos 16 ensaios.
* `fig_10c_paridade_e_residuos_xgb.png`: Gráfico de paridade 1:1 e distribuição de resíduos em escala linear.
* `fig_10c_paridade_e_residuos_xgb_log.png`: Paridade log-log (4 ordens de magnitude) e distribuição de resíduos logarítmicos.
* `fig_10d_comparativo_hiperparametros_xgb.png`: Comparação quantitativa das configurações de hiperparâmetros na validação cruzada.
