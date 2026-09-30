# Etapa 1.1: Módulo de Granulometria (`src/physics/granulometry.py`)

## Objetivo
Implementar o módulo permanente de primeiros princípios que encapsula o modelo analítico e numérico de distribuição granulométrica Rosin-Rammler-Bennet (RRB).

## Estrutura da Etapa
- **Código-fonte de produção**: [`Código/src/physics/granulometry.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/granulometry.py)
- **Script de Testes Unitários**: [`test_granulometry.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/etapas/etapa_1_1_modulo_granulometria/test_granulometry.py)

## Métodos Implementados na Classe `RosinRammlerBennet`
1. `cumulative_passing(d)`: Cálculo da fração acumulada passante $F(D)$.
2. `probability_density(d)`: Cálculo da densidade contínua $f_0(D) = dF/dD$.
3. `analytical_moment(k)`: Cálculo analítico exato do $k$-ésimo momento da distribuição via função Gama $\Gamma(1 + k/m)$.
4. `mean_diameter()`: Diâmetro médio analítico ($\bar{\mu} \approx 41,28\,\mu\text{m}$).
5. `variance()` e `coefficient_of_variation()`: Dispersão e $CV \approx 0,97$.
6. `generate_mesh(d_min, d_max, n_points)`: Geração da malha linear discretizada de nós e terceiro momento de volume $M_3(0)$.
7. `evaluate_fit(diametros, fracao_exp)`: Avaliação estatística de aderência ($R^2$, RMSE, MAE).

## Entregas (Outputs)
- [`Código/outputs/etapa_1_1/relatorio_validacao_etapa_1_1.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_1/relatorio_validacao_etapa_1_1.md): Relatório com tabela de resultados dos testes analíticos, numéricos e experimentais.
- [`Código/outputs/etapa_1_1/nota_conceitual_granulometria_RRB.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_1/nota_conceitual_granulometria_RRB.md): Nota técnica e conceitual sobre os fundamentos de RRB, momentos estatísticos e preservação do terceiro momento M3(0) no PBM.
