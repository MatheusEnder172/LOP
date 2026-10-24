# Preservação Histórica — Checkpoints dos Modelos Treinados (Abordagem Antiga sem Divisão por D³)

## 1. Contexto e Motivação
Este diretório preserva os modelos supervisionados (checkpoints `.pt`, `.joblib`) treinados para predizer a taxa de retração `|v(t)|` na escala da abordagem antiga (onde `|v₀|` atingia até ~1227 µm/min).

## 2. Conteúdo Preservado
- `mlp/`: Checkpoint PyTorch da Rede Neural (`mlp_melhor_modelo.pt`, `mlp_arquitetura_info.json`).
- `random_forest/`: Checkpoints do Random Forest (`rf_melhor_modelo.joblib`, `rf_info.json`).
- `svr/`: Checkpoints do SVR RBF (`svr_melhor_modelo.joblib`, `svr_info.json`).
- `xgboost/`: Checkpoints do XGBoost (`xgb_melhor_modelo.joblib`, `xgb_info.json`).
- `modelo_campeao_info.json`: Metadados do modelo campeão selecionado pelo método multicritério MCDA.

## 3. Substituição na Pasta Pai
Os modelos na pasta pai foram retreinados sobre os novos alvos da Fase 2 (`RRB ÷ D³`), aprendendo a nova escala física realista (`|v₀|` médio de 179,8 µm/min e `δ₅₀% = 4,83 µm`).
