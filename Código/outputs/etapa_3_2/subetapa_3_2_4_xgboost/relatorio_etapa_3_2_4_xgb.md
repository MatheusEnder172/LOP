# Relatório de Validação Técnica — Subetapa 3.2.4: XGBoost Gradient Boosting

## 1. Sumário Executivo
Nesta subetapa, implementou-se o modelo de aprendizado por árvores de decisão impulsionadas por gradiente **KineticsXGBoost** para a predição contínua da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições operacionais $[T, C_{A0}, η, t]$.

Investigaram-se cinco configurações sob o mesmo protocolo de **GroupKFold (4 dobras disjuntas por ensaio)**:
1. **XGB-Baseline (Default)**: `n_estimators=100`, `learning_rate=0.10`, `max_depth=6`.
2. **XGB-Regularizado (Shallow)**: `n_estimators=100`, `learning_rate=0.05`, `max_depth=4`, `subsample=0.80`.
3. **XGB-Profundo (Deep)**: `n_estimators=150`, `learning_rate=0.05`, `max_depth=8`.
4. **XGB-Otimizado (Campeão)**: `n_estimators=120`, `learning_rate=0.05`, `max_depth=5`, `subsample=0.85`, `colsample=0.85`.
5. **XGB-LinearTarget (Sem Log1p)**: Treinado em escala linear direta para evidenciar a necessidade de compressão logarítmica.

A configuração campeã foi a **XGB-Baseline (Default)**, alcançando **$R^2 = 0.9995$ no Treino** e **$R^2 = 0.8117$ no Teste Cego**.

---

## 2. Comparativo de Hiperparâmetros na Validação Cruzada (4 Dobras Disjuntas)

| Configuração | Estimadores | Taxa (η) | Max Depth | Subsample | Colsample | Target | $R^2$ Médio (CV) | RMSE (µm/min) | MAE (µm/min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGB-Baseline (Default)** | 100 | 0.1 | 6 | 1.0 | 1.0 | `log1p` | **0.8559 ± 0.0531** | 3.18 | 1.25 |
| **XGB-Regularizado (Shallow)** | 100 | 0.05 | 4 | 0.8 | 0.8 | `log1p` | **0.6975 ± 0.1512** | 4.69 | 1.55 |
| **XGB-Profundo (Deep)** | 150 | 0.05 | 8 | 0.8 | 0.8 | `log1p` | **0.8176 ± 0.1552** | 3.62 | 1.41 |
| **XGB-Otimizado (Campeão)** | 120 | 0.05 | 5 | 0.85 | 0.85 | `log1p` | **0.7768 ± 0.1442** | 4.03 | 1.46 |
| **XGB-LinearTarget (Sem Log1p)** | 100 | 0.05 | 5 | 0.85 | 0.85 | `linear` | **0.7648 ± 0.0693** | 4.07 | 1.77 |

---

## 3. Desempenho Global do Modelo Campeão (XGB-Baseline (Default))

* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * $R^2$: **0.9995**
  * RMSE: **0.19 µm/min**
  * MAE: **0.04 µm/min**
  * Erro Máximo: **3.72 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras intocadas: Ens 8, 14 e 7)**:
  * $R^2$: **0.8117**
  * RMSE: **3.70 µm/min**
  * MAE: **1.43 µm/min**
  * Erro Máximo: **27.97 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (restrição termodinâmica garantida estritamente).

---

## 4. Avaliação Individual nos Ensaios de Teste Cego

| Ensaio | Regime Físico-Químico | $C_{A0}$ (mol/L) | η (-) | $R^2$ Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **7** | Forte Excesso Ácido | 0.50 | 3.1 | **0.4608** | 6.37 | 3.98 |
| **8** | Estequiométrico Neutro | 0.50 | 1.0 | **0.9925** | 0.48 | 0.10 |
| **14** | Leve Excesso Ácido | 1.00 | 1.5 | **0.9965** | 0.57 | 0.22 |

---

## 5. Importância dos Atributos Físicos (Ganho de Informação e Permutação)

| Atributo | Significado Físico-Químico | Importância por Ganho (Gain) | Importância por Permutação (Teste Cego) |
| :--- | :--- | :---: | :---: |
| `t_min` | Tempo de reação (decaimento cinético rápido) | **48.1%** | **ΔR² = 2.1897 ± 0.3833** |
| `razao_molar_eta` | Razão estequiométrica (potencial termodinâmico) | **34.8%** | **ΔR² = 0.6039 ± 0.1565** |
| `CA0_mol_L` | Força motriz de concentração ácida | **17.1%** | **ΔR² = 0.1095 ± 0.0695** |

---

## 6. Figuras de Diagnóstico Geradas (300 DPI)
* `fig_10a_importancia_features_xgb.png`: Importância de atributos por Ganho e Permutação no teste cego.
* `fig_10b_predicoes_v_xgb.png`: Trajetórias temporais de $|v(t)|$ em escala linear nos 16 ensaios.
* `fig_10b_predicoes_v_xgb_log.png`: Trajetórias temporais de $|v(t)|$ em escala semilogarítmica nos 16 ensaios.
* `fig_10c_paridade_e_residuos_xgb.png`: Gráfico de paridade 1:1 e distribuição de resíduos em escala linear.
* `fig_10c_paridade_e_residuos_xgb_log.png`: Paridade log-log (4 ordens de magnitude) e distribuição de resíduos logarítmicos.
* `fig_10d_comparativo_hiperparametros_xgb.png`: Comparação quantitativa das configurações de hiperparâmetros na validação cruzada.
