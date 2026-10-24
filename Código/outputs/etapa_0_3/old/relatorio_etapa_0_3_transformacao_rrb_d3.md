# Relatório Técnico de Validação — Etapa 0.3: Transformação da Distribuição RRB (Divisão por D³) e Avaliação White-Box

**Data**: 22 de Outubro de 2026  
**Etapa**: 0.3 (`Código/etapas/etapa_0_3_transformacao_rrb_d3/`)  
**Diretório de Saídas**: `Código/outputs/etapa_0_3/`

---

## 1. Sumário Executivo

Nesta etapa foi investigado e validado o efeito da conversão da distribuição granulométrica de Rosin-Rammler-Bennet (RRB) da **base mássica** `f_m(D)` para a **base numérica** `f_n(D) ∝ f_m(D) / D³` (Equação 3.48 de Bortot Coelho, 2017), **mantendo 100% intacta a equação de conversão do Balanço Populacional (`BatchPBMSolver`)**:

- `X_Zn(δ) = 1 − [ ∫_δ^D_max (D − δ)³ · f₀(D) dD ] / [ ∫_D_min^D_max D³ · f₀(D) dD ]`

A simples correção da distribuição de entrada `f₀(D)` (dividindo a densidade RRB por `D³`) eliminou a dupla ponderação volumétrica (`D³ · f_m(D)`) que deslocava artificialmente a massa para partículas grosseiras e proporcionou um **salto expressivo de acurácia no modelo White-Box puro**, sem alterar nenhum parâmetro cinético (`k_s = 18000 μm/min` e `α = 5500 μm/min`).

---

## 2. Comparação das Propriedades Granulométricas e Mapeamento δ → X_Zn

| Propriedade Física / Estatística | Abordagem Antiga (`f₀ = f_m`, sem ÷ D³) | Nova Abordagem (`f₀ = f_n ∝ f_m / D³`) | Interpretação Física |
| :--- | :---: | :---: | :--- |
| **Peso Volumétrico no Integrando `D³ · f₀(D)`** | `D³ · f_m(D) ∝ D⁶ · f_n(D)` | `D³ · (f_m(D) / D³) = f_m(D)` | Restaura a distribuição mássica real medida no laboratório |
| **Diâmetro Médio Mássico Efetivo no PBM** | `146,9 μm` (distorcido) | **`41,6 μm`** (fiel à dissertação: `41,28 μm`) | Corrige a superestimação de 3,5× no tamanho médio efetivo |
| **Aderência da Massa do PBM à Tabela 5.4 (r²)** | Deslocada para grãos grossos | **`0,9962`** | Coincidência exata com peneiramento e difração a laser |
| **Encolhimento `δ` para `X_Zn = 50%` (`δ₅₀%`)** | `26,31 μm` | **`4,83 μm`** | Finos reagem rapidamente nos primeiros segundos |
| **Encolhimento `δ` para `X_Zn = 80%` (`δ₈₀%`)** | `59,90 μm` | **`15,90 μm`** | Escala realista de recuo interfacial |

---

## 3. Impacto Quantitativo no Modelo White-Box (16 Ensaios de Bancada — 128 Pontos)

### 3.1. Métricas Globais Consolidadas

| Modelo Mecanicista (White-Box) | Métrica Global | Sem Dividir por D³ (Antigo) | Dividindo RRB por D³ (Novo) | Variação / Ganho |
| :--- | :---: | :---: | :---: | :---: |
| **FPM Nominal (`α = 5500 μm/min`)** | **r² Global** | 0,9030 | **0,9560** | **+0,0530** |
| **FPM Nominal (`α = 5500 μm/min`)** | **RMSE Global** | 10,10% (0,1010) | **6,80% (0,0680)** | **−32,7% de redução no RMSE** |
| **FPM Nominal (`α = 5500 μm/min`)** | **MAE Global** | 6,99% (0,0699) | **5,38% (0,0538)** | **−23,0% de redução no MAE** |
| **Cinético Puro (`α = 0 μm/min`)** | **r² Global** | 0,9279 | **0,9590** | **+0,0311** |
| **Cinético Puro (`α = 0 μm/min`)** | **RMSE Global** | 8,70% (0,0870) | **6,56% (0,0656)** | **−24,6% de redução no RMSE** |

---

### 3.2. Comparação Detalhada Ensaio por Ensaio (`α = 5500 μm/min` e `α = 0 μm/min`)

| Ensaio | η | C_A0 (mol/L) | r² Antigo (α=5500) | r² Novo ÷ D³ (α=5500) | Ganho Δr² (α=5500) | RMSE Antigo (%) | RMSE Novo ÷ D³ (%) | r² Antigo (α=0) | r² Novo ÷ D³ (α=0) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **E01** | 0,5 | 0,10 | 0,5767 | **0,6759** | **+0,0992** | 10,38% | **9,09%** | 0,9519 | **0,9601** |
| **E02** | 3,1 | 0,10 | 0,7676 | **0,9940** | **+0,2264** | 15,26% | **2,46%** | 0,7876 | **0,9912** |
| **E03** | 0,5 | 0,50 | 0,6096 | **0,6102** | +0,0006 | 10,19% | **10,18%** | 0,9871 | 0,9836 |
| **E04** | 0,5 | 1,00 | 0,5625 | **0,5625** | 0,0000 | 10,98% | 10,98% | 0,9868 | 0,9868 |
| **E05** | 0,5 | 1,50 | 0,6481 | **0,6481** | 0,0000 | 9,51% | 9,51% | 0,9888 | 0,9888 |
| **E06** | 1,0 | 0,10 | 0,5317 | **0,9133** | **+0,3817** | 18,87% | **8,12%** | 0,7152 | **0,9369** |
| **E07** | 3,1 | 0,50 | 0,9919 | 0,9779 | −0,0140 | 2,91% | 4,80% | 0,9894 | 0,9772 |
| **E08** | 1,0 | 0,50 | 0,8827 | **0,9146** | **+0,0319** | 9,66% | **8,25%** | 0,9037 | 0,8548 |
| **E09** | 1,0 | 1,00 | 0,9288 | **0,9348** | +0,0061 | 7,43% | **7,11%** | 0,8223 | 0,7800 |
| **E10** | 1,0 | 1,50 | 0,9418 | **0,9437** | +0,0019 | 6,67% | **6,56%** | 0,7709 | 0,7392 |
| **E11** | 1,5 | 0,10 | 0,6209 | **0,9794** | **+0,3585** | 18,96% | **4,42%** | 0,6911 | **0,9750** |
| **E12** | 3,1 | 1,00 | 0,9983 | 0,9978 | −0,0005 | 1,36% | 1,53% | 0,9980 | 0,9978 |
| **E13** | 1,5 | 0,50 | 0,9753 | **0,9813** | +0,0060 | 4,91% | **4,28%** | 0,9799 | 0,9742 |
| **E14** | 1,5 | 1,00 | 0,9904 | 0,9832 | −0,0072 | 3,10% | 4,10% | 0,9845 | 0,9796 |
| **E15** | 1,5 | 1,50 | 0,9798 | 0,9741 | −0,0056 | 4,46% | 5,04% | 0,9735 | 0,9723 |
| **E16** | 3,1 | 1,50 | 0,9970 | 0,9969 | 0,0000 | 1,80% | 1,80% | 0,9969 | 0,9969 |

---

## 4. Principais Descobertas Físico-Químicas desta Etapa

1. **Explicação do "Mistério" dos Ensaios Diluídos (`C_A0 = 0,10 mol/L` — Ensaios 1, 2, 6 e 11)**:
   - Na dissertação de Bortot Coelho (Tabela 5.10, p. 158) e na nossa Etapa 1.3 anterior, os ensaios com `C_A0 = 0,10 mol/L` apresentavam os piores ajustes de todo o banco de dados (`r² = 0,5317` no Ensaio 6; `r² = 0,6209` no Ensaio 11; `r² = 0,7676` no Ensaio 2), porque a curva simulada subia muito lentamente nos primeiros 5 minutos.
   - Com a divisão da RRB por `D³`, descobre-se que **a lentidão artificial do modelo em `C_A0 = 0,10 mol/L` era consequência direta de usar `f_m(D)` sem dividir por `D³`**! Como em `C_A0 = 0,10 mol/L` a velocidade linear `|v(t)|` é menor, o deslocamento `δ(t)` nos primeiros 2 minutos é da ordem de `5 a 15 μm`. No modelo antigo (que achava que as partículas tinham `146,9 μm`), `δ = 10 μm` convertia quase nada; no modelo corrigido (`RRB ÷ D³`), `δ = 10 μm` já dissolve todas as partículas finas e intermediárias, fazendo o `r²` saltar:
     - **Ensaio 06 (`C_A0 = 0,10 M, η = 1,0`)**: `r²` salta de **0,5317 para 0,9133** (+0,3817)!
     - **Ensaio 11 (`C_A0 = 0,10 M, η = 1,5`)**: `r²` salta de **0,6209 para 0,9794** (+0,3585)!
     - **Ensaio 02 (`C_A0 = 0,10 M, η = 3,1`)**: `r²` salta de **0,7676 para 0,9940** (+0,2264)!
2. **O que a Divisão por D³ Resolve e o que Continua Exigindo a Modelagem Híbrida**:
   - **O que a divisão por `D³` resolve**: Corrige a escala temporal e a curvatura cinética inicial (`t < 5 min`), pois representa corretamente a área superficial e a fração mássica dos finos.
   - **O que continua exigindo o Modelo Híbrido (ML)**: O patamar assintótico de equilíbrio (`X_Zn^Max = η · k_s / (k_s + α)`) independe da distribuição granulométrica! Por isso, para `α = 5500 μm/min` fixo, o White-Box ainda estaciona em `38,3%` para `η = 0,5` (contra `50,0%` experimental) e em `76,6%` para `η = 1,0` (contra `85–87%` experimental). Isso reforça ainda mais a elegância da tese do TCC: corrigida a geometria granulométrica (`RRB ÷ D³`), resta exclusivamente ao Aprendizado de Máquina corrigir a limitação do parâmetro cinético estático `α`!
