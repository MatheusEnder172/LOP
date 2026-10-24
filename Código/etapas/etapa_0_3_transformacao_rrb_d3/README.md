# Etapa 0.3: Transformação da Distribuição Granulométrica RRB (Divisão por D³) e Impacto no Modelo White-Box

## 1. Objetivo
Realizar a conversão física e matemática da distribuição granulométrica de Rosin-Rammler-Bennet (RRB) — originalmente calibrada em **base mássica** `f_m(D)` a partir dos dados de peneiramento a úmido e difração a laser (Tabela 5.4 de Bortot Coelho, 2017) — para a **base em número de partículas** `f_n(D)`, dividindo-a por `D³` conforme a Equação (3.48) de Bortot Coelho (2017) / Herbst (1979):

- **Equação de Transformação (Massa → Número)**:
  `f_n(D) = [ D⁻³ · f_m(D) ] / [ ∫ D⁻³ · f_m(D) dD ]`

A diretriz central desta etapa é **manter 100% inalterada a equação de conversão do Balanço Populacional (`BatchPBMSolver`)**:
- **Equação de Conversão Preservada**:
  `X_Zn(δ) = 1 − [ ∫_δ^D_max (D − δ)³ · f₀(D) dD ] / [ ∫_D_min^D_max D³ · f₀(D) dD ]`

Alterando exclusivamente a distribuição de entrada `f₀(D)` de `f_m(D)` para `f_n(D)`, corrige-se a dupla ponderação volumétrica (`D³ · f_m(D) ∝ D⁶ · f_n(D)`) que ocorria no algoritmo original da dissertação (Apêndices A2.1 e A2.3).

---

## 2. Scripts Implementados nesta Pasta (`Código/etapas/etapa_0_3_transformacao_rrb_d3/`)
- [`avaliar_transformacao_rrb_d3.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/etapas/etapa_0_3_transformacao_rrb_d3/avaliar_transformacao_rrb_d3.py): Implementa a subclasse `RosinRammlerNumeroD3`, executa a análise comparativa das distribuições granulométricas e simula os 16 ensaios de bancada no modelo White-Box (`α = 5500 μm/min` e `α = 0 μm/min`).
- [`test_transformacao_rrb_d3.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/etapas/etapa_0_3_transformacao_rrb_d3/test_transformacao_rrb_d3.py): Suíte de 4 testes unitários automatizados (`pytest`) validando normalização, recuperação exata da massa experimental, conservação termodinâmica e ganho de acurácia no White-Box.

---

## 3. Artefatos e Entregas Geradas em [`Código/outputs/etapa_0_3/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/)

### 3.1. Figuras Científicas em Alta Resolução (300 DPI PNG + PDF Vetorial)
1. [`fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.png) / [`.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.pdf):
   - Painel (a): Densidade mássica `f_m(D)` vs. densidade numérica `f_n(D) ∝ f_m(D) / D³` em escala log-log.
   - Painel (b): Distribuição mássica efetiva vista pelo integrando `[D³ · f₀(D)]` (mostrando como o modelo antigo deslocava o diâmetro médio efetivo para `146,9 μm`, enquanto o modelo dividido por `D³` restaura a média real de `41,6 μm`).
   - Painel (c): Curva acumulada de massa integrada pelo PBM confrontada diretamente com os 33 pontos experimentais de peneiramento a úmido e difração a laser (r² = 0,9962).
   - Painel (d): Curva de conversão `X_Zn(δ)` vs. deslocamento diametral `δ` (`δ₅₀%` cai de `26,31 μm` para `4,83 μm`).
2. [`fig_03b_whitebox_painel_eta_antigo_vs_novo.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03b_whitebox_painel_eta_antigo_vs_novo.png) / [`.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03b_whitebox_painel_eta_antigo_vs_novo.pdf):
   - Painel 2×2 agrupado por razão molar estequiométrica (`η = 0,5; 1,0; 1,5; 3,1`) comparando o White-Box antigo vs. novo (`RRB ÷ D³`) frente aos dados experimentais.
3. [`fig_03c_whitebox_16_ensaios_grid_4x4.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03c_whitebox_16_ensaios_grid_4x4.png) / [`.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03c_whitebox_16_ensaios_grid_4x4.pdf):
   - Grade 4×4 com os 16 ensaios individuais de bancada sobrepondo Experimental, White-Box Antigo (`α = 5500`), White-Box Novo (`α = 5500, RRB ÷ D³`) e Cinético Puro Novo (`α = 0, RRB ÷ D³`).
4. [`fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.png) / [`.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.pdf):
   - Gráficos de barras de `r²` e `RMSE` por ensaio e diagramas de paridade 1:1 para `α = 5500 μm/min` e `α = 0 μm/min`.

### 3.2. Tabelas e Relatórios Técnicos (`.csv` e `.md`)
- [`tabela_comparativa_whitebox_antigo_vs_novo_d3.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/tabela_comparativa_whitebox_antigo_vs_novo_d3.csv)
- [`tabela_comparativa_distribuicoes_delta_XZn.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/tabela_comparativa_distribuicoes_delta_XZn.csv)
- [`nota_conceitual_transformacao_massa_numero_d3.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/nota_conceitual_transformacao_massa_numero_d3.md)
- [`nota_tecnica_diagnostico_eta_1_0_mineralogia_e_hibridismo.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/nota_tecnica_diagnostico_eta_1_0_mineralogia_e_hibridismo.md)
- [`relatorio_etapa_0_3_transformacao_rrb_d3.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/relatorio_etapa_0_3_transformacao_rrb_d3.md)

---

## 4. Resumo Quantitativo dos Resultados
| Modelo White-Box (16 Ensaios — 128 pontos) | Distribuição Antiga (f_m sem ÷ D³) | Nova Distribuição (f_n = f_m ÷ D³) | Ganho Obtido |
| :--- | :---: | :---: | :---: |
| **FPM Nominal (α = 5500 μm/min) — r² Global** | 0,9030 | **0,9560** | **+0,0530** |
| **FPM Nominal (α = 5500 μm/min) — RMSE Global** | 10,10% (0,1010) | **6,80% (0,0680)** | **−32,7% de erro** |
| **FPM Nominal (α = 5500 μm/min) — MAE Global** | 6,99% (0,0699) | **5,38% (0,0538)** | **−23,0% de erro** |
| **Cinético Puro (α = 0 μm/min) — r² Global** | 0,9279 | **0,9590** | **+0,0311** |
| **Cinético Puro (α = 0 μm/min) — RMSE Global** | 8,70% (0,0870) | **6,56% (0,0656)** | **−24,6% de erro** |
