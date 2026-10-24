# Preservação Histórica — Scripts da Etapa 2.1 (Abordagem Antiga sem Divisão por D³)

## 1. Contexto e Motivação
Este diretório preserva as implementações originais da Etapa 2.1 antes da introdução da transformação granulométrica `f_n(D) ∝ f_m(D) / D³`.

## 2. Conteúdo Preservado
- `otimizar_alvos_v.py`: Script de otimização inversa bi-exponencial com limites físicos dimensionados para a escala antiga de `v(t)` (até `1200 µm/min`).
- `plot_comparativo_malhas.py`: Script de geração da Figura 06 (comparação da amostragem experimental e densa).
- `test_otimizacao_inversa.py`: Testes unitários de validação da reconstrução antiga.
- `README.md`: Documentação técnica original da etapa.

## 3. Substituição na Pasta Pai
Os scripts na pasta pai foram refatorados para utilizar a nova parametrização do solver mecanicista com `RosinRammlerBennet(use_number_density_d3=True)`, operando na escala física real de partículas e gerando painéis comparativos *Antigo vs. Novo*.
