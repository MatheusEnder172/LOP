# Etapa 3.2: Treinamento e Seleção de Modelos Black-Box (DDM Puro)

Esta etapa abriga o desenvolvimento, treinamento, otimização e validação comparativa dos quatro regressores supervisionados para predição da taxa de retração interfacial |v(t)|:

1. [**Subetapa 3.2.1: Multi-Layer Perceptron (MLP em PyTorch)**](subetapa_3_2_1_mlp/) — R² Teste: 0,8297 | RMSE: 26,88 µm/min
2. [**Subetapa 3.2.2: Random Forest Regressor**](subetapa_3_2_2_random_forest/) — **CAMPEÃO** | R² Teste: **0,9120** | RMSE: **19,33 µm/min**
3. [**Subetapa 3.2.3: Support Vector Regression (SVR RBF)**](subetapa_3_2_3_svr/) — R² Teste: 0,6031 | Recorde no Ensaio 14 (R² = 0,9692)
4. [**Subetapa 3.2.4: XGBoost Gradient Boosting**](subetapa_3_2_4_xgboost/) — Vice-Campeão | R² Teste: 0,8009 | Recorde no Ensaio 8 (R² = 0,9801)
5. [**Subetapa 3.2.5: Comparação Geral e Seleção do Modelo Campeão**](subetapa_3_2_5_comparacao_campeao/) — Matriz MCDA e formalização

---

### Resumo do Modelo Campeão Selecionado para a Etapa 4
* **Modelo Campeão**: **Random Forest Regressor** (100 árvores, max_depth = 6, min_samples_leaf = 2)
* **Score MCDA**: **79,50 / 100**
* **R² Teste Cego Global**: **0,9120** (Ensaios 8, 14 e 7 totalmente intocados)
* **RMSE Teste Cego**: **19,33 µm/min** (menor erro dimensional entre todos os modelos)
* **R² Validação Cruzada (CV)**: **0,7136 ± 0,1227** (maior robustez espacial)
* **Violação Física (|v| < 0)**: **0,00%** (estritamente não-negativo via log1p)
* **Checkpoint Salvo**: `Código/outputs/models_saved/random_forest/rf_kinetics_v1.joblib`

---

### Documento Central de Diretrizes
Consulte o [**Guia Completo de Implementação da Etapa 3.2 (`GUIA_IMPLEMENTACAO_ETAPA_3_2.md`)**](GUIA_IMPLEMENTACAO_ETAPA_3_2.md) para detalhes matemáticos, arquitetura neural, protocolo de validação cruzada (`GroupKFold` de 4 dobras) e critérios de aceitação.
