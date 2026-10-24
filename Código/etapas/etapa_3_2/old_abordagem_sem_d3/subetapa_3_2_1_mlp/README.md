# Subetapa 3.2.1: Multi-Layer Perceptron (MLP em PyTorch)

Este diretório contém a implementação completa, testes unitários e rotina de treinamento da **Subetapa 3.2.1**, correspondente ao primeiro modelo de Machine Learning Black-Box (DDM puro) para a predição da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições operacionais do reator de lixiviação de zinco ($T$, $C_{A0}$, $\eta$, $t$).

---

## 1. Estrutura do Diretório

```
subetapa_3_2_1_mlp/
├── README.md                 # Este documento de referência e guia de uso
├── modelo_mlp.py             # Definição das classes KineticsMLP e MLPTrainer em PyTorch
├── treinar_avaliar_mlp.py    # Pipeline de validação cruzada (GroupKFold), treino final e diagnóstico
└── test_mlp.py               # Suíte de 5 testes unitários automatizados
```

---

## 2. Fundamentação Teórica e Arquitetura Neural

### 2.1 Formulação do Target e Não-Negatividade Física Estrita
A taxa instantânea $|v(t)|$ varia por mais de quatro ordens de magnitude (de ~0,01 µm/min na fase lenta até > 1200 µm/min no primeiro minuto). Para evitar o colapso numérico por valores extremos, o modelo atua no espaço logarítmico comprimido:
$$y_{\text{log}} = \ln(1 + |v|)$$

A camada de saída do modelo utiliza a função de ativação estritamente convexa **Softplus**:
$$\hat{y}_{\text{log}} = \text{Softplus}(z) = \ln(1 + e^z) \ge 0$$
$$\hat{v}(t) = \exp(\hat{y}_{\text{log}}) - 1 \ge 0$$

Isso garante que **sob qualquer hipótese ou extrapolação**, o modelo nunca prediga taxas de dissolução negativas ($\hat{v} \ge 0$ rigorosamente), atendendo à Restrição Inegociável de Conservação Física do projeto.

### 2.2 Blocos de Construção Internos
* **Normalização**: `LayerNorm` em cada camada oculta para estabilização de gradientes em pequenos lotes.
* **Ativação**: `GELU` (*Gaussian Error Linear Unit*), proporcionando superfícies de gradiente contínuas e suaves.
* **Otimizador**: `AdamW` com decaimento de peso ($L_2 = 10^{-4}$) e agendador `CosineAnnealingLR`.
* **Dispositivo de Execução**: CPU multithreaded (adequado para tensores tabulares de 793 amostras, executando épocas em milissegundos sem dependência de drivers CUDA legados).

---

## 3. Comparativo de Arquiteturas (Validação Cruzada GroupKFold - 4 Dobras)

Foram investigadas três configurações de complexidade crescente:

| Arquitetura | Camadas Ocultas | Parâmetros | R² Médio (CV) | RMSE Médio (µm/min) | MAE Médio (µm/min) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MLP-A (2 layers)** | `[64, 32]` | 2.497 | -0,2836 ± 0,7222 | 94,58 | 13,54 | Sub-ajuste (*underfitting*) |
| **MLP-B (3 layers)** | `[128, 64, 32]` | 11.009 | **0,2560 ± 0,2535** | **79,05** | **11,29** | **CAMPEÃ (Ótimo Viés-Variância)** |
| **MLP-C (5 layers)** | `[256, 128, 64, 32, 16]` | 45.057 | 0,2388 ± 0,1654 | 79,63 | 11,77 | Sobre-parametrização (*overfitting*) |

**Conclusão da Seleção**: A **MLP-B (3 camadas)** apresentou a melhor capacidade de generalização inter-ensaios nas dobras de validação cruzada disjuntas. A rede mais profunda de 5 camadas (MLP-C) sofreu leve sobre-parametrização frente ao tamanho amostral efetivo do particionamento por ensaios (13 grupos).

---

## 4. Desempenho do Modelo Campeão (MLP-B)

O modelo consolidado foi retreinado com todos os 13 ensaios de treino e avaliado no conjunto de **Teste Cego (183 amostras intocadas: Ensaios 8, 14 e 7)**:

### 4.1 Métricas Globais
* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * R²: **0,9987**
  * RMSE: **3,39 µm/min**
  * MAE: **0,34 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras)**:
  * R²: **0,8297**
  * RMSE: **26,88 µm/min**
  * MAE: **5,06 µm/min**
  * Violações Físicas ($|v| < 0$): **0,00%** (100% fisicamente consistente)

### 4.2 Desempenho por Ensaio de Teste Cego
* **Ensaio 14 ($\eta = 1,5$; $C_{A0} = 1,00$ mol/L)**: R² = **0,9712** | RMSE = **9,79 µm/min** | MAE = **1,71 µm/min**
* **Ensaio 8 ($\eta = 1,0$; $C_{A0} = 0,50$ mol/L)**: R² = **0,8290** | RMSE = **25,46 µm/min** | MAE = **4,21 µm/min**
* **Ensaio 7 ($\eta = 3,1$; $C_{A0} = 0,50$ mol/L)**: R² = **0,7436** | RMSE = **37,73 µm/min** | MAE = **9,25 µm/min**

---

## 5. Checkpoints e Artefatos Gerados

* **Pesos do Modelo**: `Código/outputs/models_saved/mlp/mlp_kinetics_v1.pt`
* **Metadados e Hiperparâmetros**: `Código/outputs/models_saved/mlp/mlp_config.json`
* **Relatório Técnico Completo**: `Código/outputs/etapa_3_2/subetapa_3_2_1_mlp/relatorio_etapa_3_2_1_mlp.md`
* **Tabelas de Resultados**:
  * `Código/outputs/etapa_3_2/subetapa_3_2_1_mlp/tabela_metricas_mlp.csv`
  * `Código/outputs/etapa_3_2/subetapa_3_2_1_mlp/tabela_comparativo_arquiteturas_mlp.csv`
* **Figuras Científicas em 300 DPI e PDF Vetorial**:
  * `fig_07a_curvas_aprendizado_mlp.png` / `.pdf`: Curvas de convergência de perda por época nas 4 dobras.
  * `fig_07b_predicoes_v_mlp.png` / `.pdf`: Trajetórias temporais de $|v(t)|$ preditas vs. observadas nos 16 ensaios.
  * `fig_07c_paridade_e_residuos_mlp.png` / `.pdf`: Gráficos de paridade 1:1 e histograma de resíduos.
  * `fig_07d_comparativo_arquiteturas_mlp.png` / `.pdf`: Diagrama de barras com o desempenho comparativo das três arquiteturas.

---

## 6. Como Executar

### 6.1 Testes Unitários Automatizados
```bash
pytest Código/etapas/etapa_3_2/subetapa_3_2_1_mlp/test_mlp.py -v
```

### 6.2 Execução do Treinamento e Avaliação
```bash
python Código/etapas/etapa_3_2/subetapa_3_2_1_mlp/treinar_avaliar_mlp.py
```
