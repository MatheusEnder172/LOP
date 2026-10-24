# Preservação Histórica — Splits de Treinamento/Teste (Abordagem Antiga sem Divisão por D³)

## 1. Contexto e Motivação
Este diretório armazena os splits de dados (`train_dense.csv`, `test_dense.csv`, `train_exp.csv`, `test_exp.csv`) e os scalers (`scalers.joblib`) calibrados sobre os alvos de velocidade de retração `v(t)` da abordagem antiga (sem a transformação `RRB ÷ D³`).

## 2. Conteúdo Preservado
- `train_dense.csv`: 793 amostras (13 ensaios) em malha fina regular com velocidades `|v(t)|` escaladas até ~1227 µm/min.
- `test_dense.csv`: 183 amostras (Ensaios 7, 8 e 14) para teste cego.
- `train_exp.csv`: 104 amostras nos instantes experimentais de bancada.
- `test_exp.csv`: 24 amostras nos instantes experimentais dos ensaios de teste.
- `scalers.joblib`: Parâmetros de padronização (`StandardScaler`) ajustados sobre a escala antiga de `v(t)`.
- `cv_folds_info.json`: Mapeamento de folds de validação cruzada agrupada por ensaio (GroupKFold).

## 3. Substituição na Pasta Pai
Os arquivos na pasta pai foram recalculados a partir dos novos alvos gerados na Fase 2 com a distribuição `RRB ÷ D³` (`δ₅₀% = 4,83 µm`), operando na escala física real de partículas.
