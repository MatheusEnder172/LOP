# Relatório de Validação Técnica — Subetapa 3.2.1: Multi-Layer Perceptron (MLP)

## 1. Sumário Executivo
Nesta subetapa, implementou-se o modelo de regressão neural supervisionado **KineticsMLP** em PyTorch para a predição da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições do reator $[T, C_{A0}, \eta, t]$.

Compararam-se rigorosamente três arquiteturas neurais:
* **MLP-A (2 camadas)**: `[64, 32]` (~2,4 mil parâmetros);
* **MLP-B (3 camadas)**: `[128, 64, 32]` (~11,0 mil parâmetros);
* **MLP-C (5 camadas)**: `[256, 128, 64, 32, 16]` (~45,1 mil parâmetros).

A arquitetura campeã foi a **MLP-B (3 layers)**, superando as metas de acurácia com **$R^2 = 0.9987$ no Treino** e **$R^2 = 0.8297$ no Teste Cego**.

---

## 2. Comparação de Desempenho na Validação Cruzada (4 Dobras Disjuntas)

| Arquitetura | Topologia | $R^2$ Médio (CV) | $R^2$ Desvio | RMSE Médio (µm/min) | MAE Médio (µm/min) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MLP-B (3 layers)** | `[128, 64, 32]` | **0.2560** | ±0.2535 | 79.05 | 11.29 |
| **MLP-C (5 layers)** | `[256, 128, 64, 32, 16]` | **0.2388** | ±0.1654 | 79.63 | 11.77 |
| **MLP-A (2 layers)** | `[64, 32]` | **-0.2836** | ±0.7222 | 94.58 | 13.54 |

---

## 3. Desempenho Global do Modelo Consolidado (MLP-B (3 layers))

* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * $R^2$: **0.9987**
  * RMSE: **3.39 µm/min**
  * MAE: **0.34 µm/min**
  * Erro Máximo: **82.52 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras intocadas: Ens 8, 14 e 7)**:
  * $R^2$: **0.8297**
  * RMSE: **26.88 µm/min**
  * MAE: **5.06 µm/min**
  * Erro Máximo: **271.59 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (estritamente não-negativo via Softplus).

---

## 4. Avaliação Individual nos Ensaios de Teste Cego

| Ensaio | Regime Físico-Químico | $C_{A0}$ (mol/L) | $\eta$ (-) | $R^2$ Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **8** | Estequiométrico Neutro | 0.50 | 1.0 | **0.8290** | 25.46 | 4.21 |
| **14** | Leve Excesso Ácido | 1.00 | 1.5 | **0.9712** | 9.79 | 1.71 |
| **7** | Forte Excesso Ácido | 0.50 | 3.1 | **0.7436** | 37.73 | 9.25 |

---

## 5. Figuras de Diagnóstico Geradas (300 DPI)
* `fig_07a_curvas_aprendizado_mlp.png`: Perdas de treino e validação por época nas 4 dobras do GroupKFold.
* `fig_07b_predicoes_v_mlp.png`: Trajetórias temporais de $|v(t)|$ preditas pelo MLP vs. alvos exatos nos 16 ensaios.
* `fig_07c_paridade_e_residuos_mlp.png`: Gráfico de paridade 1:1 e distribuição estatística de resíduos.
* `fig_07d_comparativo_arquiteturas_mlp.png`: Comparação quantitativa das arquiteturas A, B e C na validação cruzada.
