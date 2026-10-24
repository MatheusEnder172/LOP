# Relatório Técnico — Etapa 0.3: Transformação da Distribuição Granulométrica RRB (Divisão por D³) e Avaliação no Modelo White-Box Puro (Sem Parâmetro α)

## 1. Resumo Executivo e Motivação

Neste relatório documentamos a **Etapa 0.3**, na qual avaliamos o impacto de transformar a função densidade de probabilidade granulométrica de Rosin-Rammler-Bennet (RRB) de **base mássica** (`f_m(D)`) para **base numérica** (`f_n(D) ∝ f_m(D) / D³`), **sem alterar a equação de conversão** do [`BatchPBMSolver`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/src/physics/pbm_batch.py) e **sem considerar o parâmetro empírico de amortecimento cinético `α` (`α = 0`)**.

---

## 2. Por que o gráfico antigo da Etapa 0.2 (`fig_02_granulometria_RRB.png`) já coincidia com a curva "Nova" dentro do PBM?

Na **Etapa 0.2** ([`fig_02_granulometria_RRB.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_2/fig_02_granulometria_RRB.png)), o gráfico apresentava o ajuste da equação de Rosin-Rammler-Bennet **isoladamente** (`F_m(D)` e sua derivada `f_m(D) = dF_m/dD`, com diâmetro médio `41,28 μm` e `D_63,2 = 41,65 μm`) diretamente sobre os dados experimentais de peneiramento a úmido e difração a laser (Tabela 5.4 de Bortot Coelho, 2017) — isto é, **antes** de entrar na equação de conversão do Balanço Populacional.

O problema físico-matemático surgia **no passo seguinte**, quando o solver do Balanço Populacional ([`BatchPBMSolver`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/src/physics/pbm_batch.py)) inseria a distribuição inicial `f₀(D)` na equação de conversão:

`X_Zn(δ) = 1 − [ ∫ (D − δ)³ · f₀(D) dD ] / [ ∫ D³ · f₀(D) dD ]`

1. **No PBM Antigo (sem dividir a RRB por `D³`)**:
   - A função `f₀(D)` recebida pelo solver era a própria `f_m(D)` da Etapa 0.2 (que já está ponderada em massa/volume).
   - Quando a equação de conversão multiplicava `f₀(D)` por `D³` no integrando (`D³ · f_m(D)`), a distribuição sofria uma **segunda ponderação volumétrica espúria** (`D³ · f_m(D) ∝ D⁶ · f_n(D)`).
   - Com isso, dentro do PBM Antigo, a curva deixava de ser a curva da Etapa 0.2 (`média = 41,6 μm`) e se transformava na curva tracejada azul distorcida com **diâmetro médio efetivo de `146,9 μm`**!
2. **No PBM Novo da Etapa 0.3 (dividindo a RRB por `D³`)**:
   - Antes de entrar na equação de conversão, dividimos a RRB da Etapa 0.2 por `D³`: `f₀(D) = f_n(D) ∝ f_m(D) / D³` (curva vermelha do painel `a` de [`fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.png)).
   - Quando essa `f_n(D)` entra na equação de conversão e o solver a multiplica por `D³`, ocorre o cancelamento exato:
     `D³ · f_n(D) ∝ D³ · [ f_m(D) / D³ ] = f_m(D)`
   - Por isso, **dentro da equação de conversão**, a curva efetiva do PBM Novo (curva verde dos painéis `b` e `c` da Figura 03a) **recupera exatamente a curva experimental da Etapa 0.2** (`fig_02_granulometria_RRB.png`)!

---

## 3. Resultados do Modelo White-Box Puro (Sem Parâmetro α) nos 16 Ensaios

Ao avaliar o modelo White-Box mecanicista puro **sem o parâmetro empírico `α` (`α = 0`)**, isolamos o efeito exclusivo da cinética intrínseca e da geometria granulométrica:

### 3.1. Métricas Globais (16 Ensaios, 128 Pontos Experimentais)

| Configuração do White-Box Puro (Sem `α`) | `r²` Global | `RMSE` Global (`X_Zn`) | `MAE` Global (`X_Zn`) | Redução Relativa de `RMSE` |
| :--- | :---: | :---: | :---: | :---: |
| **White-Box Antigo (Sem `α`, RRB `f_m` direto)** | `0,9279` | `0,0870` (`8,70%`) | `0,0506` (`5,06%`) | *Baseline* |
| **White-Box Novo (Sem `α`, RRB `f_n ∝ f_m / D³`)** | **`0,9590`** | **`0,0656` (`6,56%`)** | **`0,0451` (`4,51%`)** | **−24,6%** |

### 3.2. Desempenho Individual por Ensaio (White-Box Sem `α`)

| Ensaio | `C_A0` (mol/L) | `η` | `r²` Antigo (Sem `α`) | `r²` Novo (`RRB ÷ D³`, Sem `α`) | Ganho `Δr²` | `RMSE` Antigo (%) | `RMSE` Novo (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | `0,10` | `0,5` | `0,9519` | **`0,9601`** | `+0,0082` | `3,50%` | **`3,19%`** |
| **02** | `0,10` | `3,1` | `0,7876` | **`0,9912`** | **`+0,2036`** | `14,59%` | **`2,98%`** |
| **03** | `0,50` | `0,5` | `0,9871` | `0,9836` | `−0,0035` | `1,85%` | `2,09%` |
| **04** | `1,00` | `0,5` | `0,9868` | `0,9868` | `0,0000` | `1,90%` | `1,90%` |
| **05** | `1,50` | `0,5` | `0,9888` | `0,9888` | `0,0000` | `1,70%` | `1,70%` |
| **06** | `0,10` | `1,0` | `0,7152` | **`0,9369`** | **`+0,2217`** | `14,71%` | **`6,92%`** |
| **07** | `0,50` | `3,1` | `0,9894` | `0,9772` | `−0,0122` | `3,33%` | `4,88%` |
| **08** | `0,50` | `1,0` | `0,9037` | `0,8548` | `−0,0489` | `8,75%` | `10,75%` |
| **09** | `1,00` | `1,0` | `0,8223` | `0,7800` | `−0,0424` | `11,73%` | `13,06%` |
| **10** | `1,50` | `1,0` | `0,7709` | `0,7392` | `−0,0317` | `13,23%` | `14,12%` |
| **11** | `0,10` | `1,5` | `0,6911` | **`0,9750`** | **`+0,2838`** | `17,12%` | **`4,87%`** |
| **12** | `1,00` | `3,1` | `0,9980` | `0,9978` | `−0,0002` | `1,46%` | `1,54%` |
| **13** | `0,50` | `1,5` | `0,9799` | `0,9742` | `−0,0057` | `4,44%` | `5,03%` |
| **14** | `1,00` | `1,5` | `0,9845` | `0,9796` | `−0,0049` | `3,95%` | `4,52%` |
| **15** | `1,50` | `1,5` | `0,9735` | `0,9723` | `−0,0012` | `5,11%` | `5,22%` |
| **16** | `1,50` | `3,1` | `0,9969` | `0,9969` | `0,0000` | `1,80%` | `1,80%` |

### 3.3. Interpretação Físico-Química dos Resultados Sem `α`

1. **Correção dramática nos ensaios diluídos (`C_A0 = 0,10 mol/L` — Ensaios 01, 02, 06 e 11)**:
   - Como a taxa de encolhimento diametral `dδ/dt ∝ C_A` é baixa em meio diluído, o modelo antigo (que imaginava partículas gigantes de `146,9 μm`) subestimava severamente a conversão nos primeiros 5 minutos.
   - Ao dividir a RRB por `D³`, o modelo passa a enxergar a verdadeira fração de partículas finas (`41,6 μm`), elevando o `r²` de **`0,788 → 0,991` no Ensaio 02**, **`0,715 → 0,937` no Ensaio 06** e **`0,691 → 0,975` no Ensaio 11**!
2. **Por que nos ensaios estequiométricos concentrados (`η = 1,0`, Ensaios 08, 09 e 10) a curva sem `α` fica acima dos pontos experimentais (~85%)?**
   - Sem o parâmetro empírico `α`, o modelo White-Box assume que todo o zinco do ustulado é óxido de zinco puro (`ZnO`) altamente reativo e converge assintoticamente para `X_Zn → 1,00` (100%).
   - Experimentalmente, porém, cerca de `13% a 15%` do zinco no concentrado ustulado industrial está na forma de **ferrita de zinco (`ZnO·Fe₂O₃`, franklinita)**, que é refratária nas condições brandas de lixiviação neutra (`T = 60 °C`) quando o ácido se aproxima da exaustão estequiométrica (`η = 1,0`).

---

## 4. Índice de Artefatos da Etapa 0.3

- [`fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.png) | [`.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.pdf)
- [`fig_03b_whitebox_painel_eta_antigo_vs_novo.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03b_whitebox_painel_eta_antigo_vs_novo.png) | [`.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03b_whitebox_painel_eta_antigo_vs_novo.pdf)
- [`fig_03c_whitebox_16_ensaios_grid_4x4.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03c_whitebox_16_ensaios_grid_4x4.png) | [`.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03c_whitebox_16_ensaios_grid_4x4.pdf)
- [`fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.png) | [`.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.pdf)
- [`tabela_comparativa_whitebox_antigo_vs_novo_d3.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/tabela_comparativa_whitebox_antigo_vs_novo_d3.csv)
- [`nota_conceitual_transformacao_massa_numero_d3.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/nota_conceitual_transformacao_massa_numero_d3.md)
- [`nota_tecnica_diagnostico_eta_1_0_mineralogia_e_hibridismo.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/nota_tecnica_diagnostico_eta_1_0_mineralogia_e_hibridismo.md)
- [`old/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/C%C3%B3digo/outputs/etapa_0_3/old/README.md): Versões anteriores das figuras que incluíam `α = 5500 μm/min`, preservadas conforme a Regra 5 de governança.
