# Subetapa 3.2.2: Random Forest Regressor

Este diretório contém a implementação completa, testes unitários, rotina de validação cruzada por ensaios e treinamento da **Subetapa 3.2.2**, correspondente ao segundo modelo de Machine Learning Black-Box (DDM puro) para a predição da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições operacionais do reator de lixiviação de zinco ($T$, $C_{A0}$, $\eta$, $t$).

---

## 1. Estrutura do Diretório

```
subetapa_3_2_2_random_forest/
├── README.md                 # Este documento de referência e guia técnico
├── modelo_rf.py              # Classe KineticsRandomForest encapsulando scikit-learn
├── treinar_avaliar_rf.py     # Pipeline de CV (GroupKFold), tuning, treino e diagnóstico
└── test_rf.py                # Suíte de 6 testes unitários automatizados
```

---

## 2. Fundamentação Teórica e Modelagem Física

### 2.1 Formulação do Target e Não-Negatividade Física Estrita
A taxa de dissolução $|v(t)|$ varia por mais de quatro ordens de magnitude. No Random Forest padrão com erro quadrático (MSE), a busca de divisões em escala linear direta concentra-se quase exclusivamente nos poucos pontos iniciais ultra-rápidos ($t < 0,5$ min, onde $|v| > 500$ µm/min), ignorando a fase lenta e gerando degraus artificiais.

Para contornar esse problema e estabilizar o ajuste em toda a escala temporal:
$$y_{\text{log}} = \ln(1 + |v|)$$
$$\hat{v}(t) = \max\left(0, \exp(\hat{y}_{\text{log}}) - 1\right)$$

Como as predições de árvores de regressão para folhas não-negativas são médias amostrais de valores estritamente positivos, tem-se matematicamente $\hat{y}_{\text{log}} \ge 0 \implies \hat{v}(t) \ge 0$, eliminando qualquer risco de violação termodinâmica (0,00% de predições negativas).

---

## 3. Comparativo de Hiperparâmetros na Validação Cruzada (GroupKFold — 4 Dobras)

Foram investigadas cinco configurações de hiperparâmetros nas 4 dobras disjuntas por ensaio:

| Configuração | Estimadores | Max Depth | Min Split | Min Leaf | Target | R² Médio (CV) | RMSE Médio (µm/min) | MAE Médio (µm/min) | Diagnóstico |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **RF-Baseline (Default)** | 100 | None | 2 | 1 | `log1p` | 0,6676 ± 0,1056 | 51,33 | 9,39 | Árvores muito profundas |
| **RF-Regularizado (Shallow)** | 100 | 6 | 5 | 2 | `log1p` | **0,7136 ± 0,1227** | **48,09** | **8,65** | **CAMPEÃ (Maior Generalização)** |
| **RF-Profundo (Deep Ensemble)** | 200 | 12 | 2 | 1 | `log1p` | 0,6505 ± 0,1048 | 52,31 | 9,45 | Leve sobre-ajuste |
| **RF-Robusto (Ampla)** | 300 | 10 | 4 | 2 | `log1p` | 0,7094 ± 0,1301 | 48,62 | 8,83 | Desempenho próximo à campeã |
| **RF-LinearTarget (Sem Log1p)** | 100 | 10 | 4 | 2 | `linear` | 0,6587 ± 0,1082 | 50,90 | 9,23 | Pior ajuste na fase lenta |

**Conclusão da Seleção**: A configuração **RF-Regularizado (Shallow: `max_depth=6`, `min_samples_leaf=2`)** venceu a validação cruzada com R² de **0,7136**, superando tanto a floresta sem poda (0,6676) quanto a versão sem transformação logarítmica (0,6587). A restrição de profundidade impede que as árvores criem divisões excessivamente ruidosas para ensaios atípicos, suavizando as curvas cinéticas.

---

## 4. Desempenho do Modelo Campeão Consolidado

O modelo campeão foi retreinado com todos os 13 ensaios de treino e testado no conjunto de **Teste Cego (183 amostras intocadas: Ensaios 8, 14 e 7)**:

### 4.1 Métricas Globais
* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * R²: **0,8368**
  * RMSE: **37,59 µm/min**
  * MAE: **5,13 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras)**:
  * R²: **0,9120** (superior ao MLP: 0,8297)
  * RMSE: **19,33 µm/min** (inferior ao MLP: 26,88 µm/min)
  * MAE: **5,15 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (100% fisicamente consistente)

### 4.2 Desempenho por Ensaio de Teste Cego
* **Ensaio 8 ($\eta = 1,0$; $C_{A0} = 0,50$ mol/L — Estequiométrico Neutro)**: R² = **0,9496** | RMSE = **13,82 µm/min** | MAE = **2,85 µm/min**
* **Ensaio 14 ($\eta = 1,5$; $C_{A0} = 1,00$ mol/L — Leve Excesso Ácido)**: R² = **0,9168** | RMSE = **16,64 µm/min** | MAE = **3,96 µm/min**
* **Ensaio 7 ($\eta = 3,1$; $C_{A0} = 0,50$ mol/L — Forte Excesso Ácido)**: R² = **0,8824** | RMSE = **25,55 µm/min** | MAE = **8,63 µm/min**

---

## 5. Interpretabilidade e Importância de Atributos Físicos

| Atributo | Significado Físico-Químico | Importância MDI (Gini) | Importância por Permutação (Teste Cego) |
| :--- | :--- | :---: | :---: |
| `t_min` | Tempo de reação (decaimento exponencial rápido) | **69,5%** | **ΔR² = 1,9503 ± 0,1291** |
| `razao_molar_eta` | Razão estequiométrica (disponibilidade ácida) | **18,6%** | ΔR² residual (interação com tempo) |
| `CA0_mol_L` | Concentração inicial de H₂SO₄ (força motriz inicial) | **11,9%** | ΔR² residual |
| `temperatura_C` | Temperatura do reator (invariante em bancada: 40 °C) | **0,0%** | ΔR² = 0,0000 |

A análise comprova que a dinâmica temporal $t$ e a disponibilidade molar $\eta$ são os dois principais motores governantes da taxa de reação, em perfeita concordância com a fenomenologia hidrometalúrgica.

---

## 6. Checkpoints e Artefatos Gerados

* **Modelo Serializado**: `Código/outputs/models_saved/random_forest/rf_kinetics_v1.joblib`
* **Metadados e Hiperparâmetros**: `Código/outputs/models_saved/random_forest/rf_config.json`
* **Guia Didático e Teórico**: [`fundamentacao_e_aplicacao_random_forest_LOP.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_3_2/subetapa_3_2_2_random_forest/fundamentacao_e_aplicacao_random_forest_LOP.md)
* **Relatório Técnico Completo**: `Código/outputs/etapa_3_2/subetapa_3_2_2_random_forest/relatorio_etapa_3_2_2_rf.md`
* **Tabelas de Resultados**:
  * `Código/outputs/etapa_3_2/subetapa_3_2_2_random_forest/tabela_metricas_rf.csv`
  * `Código/outputs/etapa_3_2/subetapa_3_2_2_random_forest/tabela_comparativo_hiperparametros_rf.csv`
* **Figuras Científicas em 300 DPI e PDF Vetorial**:
  * `fig_08a_importancia_features_rf.png` / `.pdf`: Importância de atributos MDI e permutação.
  * `fig_08b_predicoes_v_rf.png` / `.pdf`: Trajetórias temporais de $|v(t)|$ preditas vs. observadas nos 16 ensaios.
  * `fig_08c_paridade_e_residuos_rf.png` / `.pdf`: Diagramas de paridade 1:1 e distribuição de resíduos.
  * `fig_08d_comparativo_hiperparametros_rf.png` / `.pdf`: Comparativo quantitativo de R² e RMSE entre as configurações avaliadas.

---

## 7. Como Executar

### 7.1 Testes Unitários Automatizados
```bash
pytest Código/etapas/etapa_3_2/subetapa_3_2_2_random_forest/test_rf.py -v
```

### 7.2 Execução do Treinamento e Avaliação
```bash
python Código/etapas/etapa_3_2/subetapa_3_2_2_random_forest/treinar_avaliar_rf.py
```
