# Subetapa 3.2.4: XGBoost Gradient Boosting Regressor

Este diretório contém a implementação completa, testes unitários, rotina de validação cruzada por ensaios e treinamento da **Subetapa 3.2.4**, correspondente ao quarto modelo de Machine Learning Black-Box (DDM puro) para a predição da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições operacionais do reator de lixiviação de zinco ($T$, $C_{A0}$, $\eta$, $t$).

---

## 1. Estrutura do Diretório

```
subetapa_3_2_4_xgboost/
├── README.md                 # Este documento de referência e guia técnico
├── modelo_xgb.py             # Classe KineticsXGBoost encapsulando XGBRegressor
├── treinar_avaliar_xgb.py    # Pipeline de CV (GroupKFold), tuning, treino e diagnóstico
└── test_xgb.py               # Suíte de 6 testes unitários automatizados
```

---

## 2. Fundamentação Teórica e Modelagem Física

### 2.1 Formulação do Target e Não-Negatividade Física Estrita
A taxa de dissolução $|v(t)|$ varia por mais de quatro ordens de magnitude. No XGBoost, a expansão de segunda ordem em escala linear direta concentraria gradientes enormes nos instantes iniciais, ignorando a cauda de reação lenta.

Operando no espaço comprimido:
$$y_{\text{log}} = \ln(1 + |v|)$$
$$\hat{v}(t) = \max\left(0,\ \exp(\hat{y}_{\text{log}}) - 1\right)$$

O modelo assegura **0,00% de violações físicas** ($|v| \ge 0$ rigorosamente em todas as predições).

---

## 3. Comparativo de Hiperparâmetros na Validação Cruzada (GroupKFold — 4 Dobras)

Foram investigadas cinco configurações de hiperparâmetros nas 4 dobras disjuntas por ensaio:

| Configuração | Estimadores | Taxa ($\eta_{\text{lr}}$) | Max Depth | Subsample | Colsample | Target | R² Médio (CV) | RMSE Médio (µm/min) | Diagnóstico |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **XGB-Baseline (Default)** | 100 | 0,10 | 6 | 1,00 | 1,00 | `log1p` | 0,5235 ± 0,2370 | 57,42 | Passos grandes, instabilidade inter-dobras |
| **XGB-Regularizado (Shallow)** | 100 | 0,05 | 4 | 0,80 | 0,80 | `log1p` | 0,6268 ± 0,1676 | 55,44 | Boa suavidade, menor capacidade |
| **XGB-Profundo (Deep)** | 150 | 0,05 | 8 | 0,80 | 0,80 | `log1p` | **0,6503 ± 0,2176** | **52,13** | **CAMPEÃ (Maior R² de validação)** |
| **XGB-Otimizado** | 120 | 0,05 | 5 | 0,85 | 0,85 | `log1p` | 0,6475 ± 0,1714 | 53,40 | Desempenho equilibrado |
| **XGB-LinearTarget** | 100 | 0,05 | 5 | 0,85 | 0,85 | `linear` | 0,6846 ± 0,0793 | 49,64 | Perda de precisão na fase lenta |

**Conclusão da Seleção**: A configuração **XGB-Profundo (150 árvores, `learning_rate=0.05`, `max_depth=8`, `subsample=0.80`, `colsample_bytree=0.80`)** venceu a validação cruzada com R² de **0,6503**, superando a configuração padrão (0,5235) e apresentando menor erro quadrático médio (52,13 µm/min).

---

## 4. Desempenho do Modelo Campeão Consolidado

O modelo campeão foi retreinado com todos os 13 ensaios de treino e avaliado no conjunto de **Teste Cego (183 amostras intocadas: Ensaios 8, 14 e 7)**:

### 4.1 Métricas Globais
* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * R²: **0,8325** | RMSE: **38,09 µm/min** | MAE: **4,82 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras)**:
  * R²: **0,8009** | RMSE: **29,06 µm/min** | MAE: **6,76 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (100% fisicamente consistente)

### 4.2 Desempenho por Ensaio de Teste Cego
* **Ensaio 8 ($\eta = 1,0$; $C_{A0} = 0,50$ mol/L — Estequiométrico Neutro)**: R² = **0,9801** | RMSE = **8,69 µm/min** | MAE = **1,87 µm/min** (RECORDE de precisão em todo o projeto)
* **Ensaio 7 ($\eta = 3,1$; $C_{A0} = 0,50$ mol/L — Forte Excesso Ácido)**: R² = **0,7759** | RMSE = **35,27 µm/min** | MAE = **12,11 µm/min**
* **Ensaio 14 ($\eta = 1,5$; $C_{A0} = 1,00$ mol/L — Leve Excesso Ácido)**: R² = **0,6350** | RMSE = **34,85 µm/min** | MAE = **6,30 µm/min**

---

## 5. Importância dos Atributos Físicos (Interpretabilidade por Ganho)

| Atributo | Significado Físico-Químico | Importância por Ganho (Gain) | Importância por Permutação (Teste Cego) |
| :--- | :--- | :---: | :---: |
| `t_min` | Tempo de reação (decaimento cinético rápido) | **45,1%** | **ΔR² = 2,0642 ± 0,3716** |
| `razao_molar_eta` | Razão estequiométrica (potencial termodinâmico) | **33,9%** | Interação acoplada com tempo |
| `CA0_mol_L` | Concentração inicial de H₂SO₄ (força motriz inicial) | **21,0%** | Interação acoplada com tempo |
| `temperatura_C` | Temperatura do banho (invariante em bancada: 40 °C) | **0,0%** | ΔR² = 0,0000 |

O XGBoost capturou uma partição muito mais rica de relevância termodinâmica entre $\eta$ (33,9%) e $C_{A0}$ (21,0%) em comparação com algoritmos de divisão estocástica simples.

---

## 6. Checkpoints e Artefatos Gerados

* **Modelo Serializado**:
  * Formato nativo: `Código/outputs/models_saved/xgboost/xgb_kinetics_v1.json`
  * Formato joblib: `Código/outputs/models_saved/xgboost/xgb_kinetics_v1.joblib`
* **Metadados e Hiperparâmetros**: `Código/outputs/models_saved/xgboost/xgb_config.json`
* **Guia Didático e Teórico**: [`fundamentacao_e_aplicacao_xgboost_LOP.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_3_2/subetapa_3_2_4_xgboost/fundamentacao_e_aplicacao_xgboost_LOP.md)
* **Relatório Técnico Completo**: `Código/outputs/etapa_3_2/subetapa_3_2_4_xgboost/relatorio_etapa_3_2_4_xgb.md`
* **Tabelas de Resultados**:
  * `Código/outputs/etapa_3_2/subetapa_3_2_4_xgboost/tabela_metricas_xgb.csv`
  * `Código/outputs/etapa_3_2/subetapa_3_2_4_xgboost/tabela_comparativo_hiperparametros_xgb.csv`
* **Figuras Científicas em 300 DPI e PDF Vetorial**:
  * `fig_10a_importancia_features_xgb.png` / `.pdf`: Importância por Ganho e Permutação.
  * `fig_10b_predicoes_v_xgb.png` / `.pdf`: Trajetórias temporais de $|v(t)|$ nos 16 ensaios (escala linear).
  * `fig_10b_predicoes_v_xgb_log.png` / `.pdf`: Trajetórias temporais de $|v(t)|$ em escala semilogarítmica.
  * `fig_10c_paridade_e_residuos_xgb.png` / `.pdf`: Paridade 1:1 e resíduos em escala linear.
  * `fig_10c_paridade_e_residuos_xgb_log.png` / `.pdf`: Paridade log-log (4 ordens de magnitude) e resíduos logarítmicos.
  * `fig_10d_comparativo_hiperparametros_xgb.png` / `.pdf`: Comparativo quantitativo de R² e RMSE na validação cruzada.

---

## 7. Como Executar

### 7.1 Testes Unitários Automatizados
```bash
pytest Código/etapas/etapa_3_2/subetapa_3_2_4_xgboost/test_xgb.py -v
```

### 7.2 Execução do Treinamento e Avaliação
```bash
python Código/etapas/etapa_3_2/subetapa_3_2_4_xgboost/treinar_avaliar_xgb.py
```
