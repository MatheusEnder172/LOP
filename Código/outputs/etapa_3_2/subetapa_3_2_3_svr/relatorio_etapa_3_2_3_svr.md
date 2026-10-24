# Relatório de Validação Técnica — Subetapa 3.2.3: Support Vector Regression (SVR RBF)

## 1. Sumário Executivo
Nesta subetapa, implementou-se o modelo de aprendizado por vetores de suporte **KineticsSVR** com kernel de base radial (RBF) para a predição contínua da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições do reator $[T, C_{A0}, η, t]$.

Investigaram-se cinco configurações sob o mesmo protocolo de **GroupKFold (4 dobras disjuntas por ensaio)**:
1. **SVR-Baseline (Default)**: `C=1.0`, `epsilon=0.10`, `gamma='scale'`.
2. **SVR-Regularizado (Tubo Largo)**: `C=10.0`, `epsilon=0.20`, `gamma=0.10`.
3. **SVR-Acurado (Tubo Estreito)**: `C=50.0`, `epsilon=0.02`, `gamma=0.25`.
4. **SVR-Otimizado (Campeão)**: `C=25.0`, `epsilon=0.05`, `gamma='scale'`.
5. **SVR-LinearTarget (Sem Log1p)**: Treinado em escala linear direta para evidenciar a necessidade de compressão logarítmica.

A configuração campeã foi a **SVR-Otimizado (Campeão)**, alcançando **$R^2 = 0.9610$ no Treino** e **$R^2 = 0.9041$ no Teste Cego**.

---

## 2. Comparativo de Hiperparâmetros na Validação Cruzada (4 Dobras Disjuntas)

| Configuração | C | Epsilon (ε) | Gamma (γ) | Target | $R^2$ Médio (CV) | RMSE (µm/min) | MAE (µm/min) | SVs Médios |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SVR-Baseline (Default)** | 1.0 | 0.1 | `scale` | `log1p` | **0.2316 ± 0.1904** | 7.16 | 2.07 | 156 |
| **SVR-Regularizado (Tubo Largo)** | 10.0 | 0.2 | `0.1` | `log1p` | **0.3170 ± 0.2606** | 6.64 | 2.21 | 130 |
| **SVR-Acurado (C=25)** | 25.0 | 0.05 | `scale` | `log1p` | **0.4969 ± 0.2506** | 5.40 | 1.88 | 180 |
| **SVR-Otimizado (Campeão)** | 100.0 | 0.1 | `0.5` | `log1p` | **0.5120 ± 0.1774** | 5.75 | 2.77 | 105 |
| **SVR-LinearTarget (Sem Log1p)** | 10.0 | 1.0 | `scale` | `linear` | **0.2854 ± 0.1011** | 6.95 | 2.40 | 103 |

---

## 3. Desempenho Global do Modelo Campeão (SVR-Otimizado (Campeão))

* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * $R^2$: **0.9610**
  * RMSE: **1.72 µm/min**
  * MAE: **0.36 µm/min**
  * Erro Máximo: **26.44 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras intocadas: Ens 8, 14 e 7)**:
  * $R^2$: **0.9041**
  * RMSE: **2.64 µm/min**
  * MAE: **1.09 µm/min**
  * Erro Máximo: **18.37 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (garantida via projeção de não-negatividade).
* **Propriedades da Formulação Dual**:
  * Vetores de Suporte Ativos: **136 / 780 (17.4%)**
  * Esparsidade Efetiva: **82.6% das amostras são irrelevantes para a inferência**, provando alta generalização.

---

## 4. Avaliação Individual nos Ensaios de Teste Cego

| Ensaio | Regime Físico-Químico | $C_{A0}$ (mol/L) | η (-) | $R^2$ Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **7** | Forte Excesso Ácido | 0.50 | 3.1 | **0.8638** | 3.20 | 2.23 |
| **8** | Estequiométrico Neutro | 0.50 | 1.0 | **0.8058** | 2.43 | 0.47 |
| **14** | Leve Excesso Ácido | 1.00 | 1.5 | **0.9490** | 2.19 | 0.57 |

---

## 5. Figuras de Diagnóstico Geradas (300 DPI)
* `fig_09a_vetores_suporte_e_sensibilidade_svr.png`: Diagnóstico espacial dos vetores de suporte no tempo e distribuição por regime de η.
* `fig_09b_predicoes_v_svr.png`: Trajetórias temporais de $|v(t)|$ preditas pelo SVR vs. alvos exatos nos 16 ensaios.
* `fig_09c_paridade_e_residuos_svr.png`: Gráfico de paridade 1:1 e distribuição estatística de resíduos.
* `fig_09d_comparativo_hiperparametros_svr.png`: Comparação quantitativa das configurações de hiperparâmetros na validação cruzada.
