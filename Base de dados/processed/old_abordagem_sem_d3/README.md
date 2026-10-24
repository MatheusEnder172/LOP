# Preservação Histórica — Datasets da Etapa 2.1 (Abordagem Antiga sem Divisão por D³)

## 1. Contexto e Motivação
Este diretório armazena os datasets de alvos de velocidade de retração gerados pela otimização bi-exponencial da Etapa 2.1 **antes** da introdução da correção da distribuição de Rosin-Rammler-Bennet (`f_n(D) ∝ f_m(D) / D³`).

## 2. Conteúdo Preservado
- `alvos_v_treinamento.csv`: 128 registros nos instantes experimentais de bancada contendo as variáveis de processo, conversão experimental, conversão reconstruída, retração diametral `δ` e velocidade `v(t)`.
- `alvos_v_treinamento_denso.csv`: 976 registros gerados em malha fina (passo 0,25 min, 61 pontos por ensaio) para treinamento supervisionado dos modelos de Machine Learning (Fase 3).
- `parametros_otimizacao_inversa.csv`: Parâmetros ótimos da bi-exponencial (`a₁`, `b₁`, `a₂`, `b₂`, `c`) e métricas de aderência (`r²`, `RMSE`, `MAE`) para cada um dos 16 ensaios experimentais.

## 3. Características Físicas da Abordagem Antiga
- Na formulação original da dissertação de Fabrício Bortot Coelho (2017), a distribuição mássica `f_m(D)` foi utilizada como se fosse numérica dentro do integrando `D³ · f(D)`, gerando uma dupla ponderação que distorceu o diâmetro médio aparente para **146,9 µm**.
- Para compensar essa distorção e atingir 50% de conversão, o solver exigia um encolhimento diametral `δ₅₀% = 26,31 µm`, elevando artificialmente as velocidades iniciais de retração até ordens de grandeza de centenas a milhares de `µm/min` (`|v₀|` de até `1227 µm/min`).
- Na **Nova Abordagem (`RRB ÷ D³`)**, o diâmetro médio real de **41,6 µm** é recuperado, de forma que `δ₅₀% = 4,83 µm` (uma escala ~5,4 vezes menor), gerando novas velocidades fisicamente realistas que substituem os arquivos na pasta pai.
