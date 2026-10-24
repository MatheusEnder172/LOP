# Nota Conceitual: Transformação da Distribuição RRB de Base Mássica para Base Numérica (Divisão por D³)

**Etapa**: 0.3 — Transformação Granulométrica RRB (÷ D³) e Avaliação no Modelo White-Box  
**Contexto**: Fundamentação físico-matemática da conversão da distribuição granulométrica de Rosin-Rammler-Bennet (RRB) de fração mássica `f_m(D)` para densidade numérica de partículas `f_n(D)`, preservando integralmente a equação clássica de conversão do Balanço Populacional.

---

## 1. Origem do Problema na Literatura de Referência (Bortot Coelho, 2017)

Na dissertação de mestrado de Fabrício Bortot Coelho (PPGEM/UFMG, 2017), a caracterização granulométrica do concentrado ustulado de zinco (calcina da Nexa Resources) foi realizada combinando peneiramento a úmido (38 a 297 μm) e difração a laser (0,45 a 74 μm), conforme reportado na Tabela 5.4 (p. 129).

Ambas as técnicas experimentais medem a **fração acumulada passante em base mássica (ou volumétrica)**, descrita pelo modelo de Rosin-Rammler-Bennet (RRB):

- **Fração Acumulada Passante (Base Mássica)**:
  `F_m(D) = 1 − exp[ −(D / D₆₃,₂)^m ]`,   com `D₆₃,₂ = 41,65 μm` e `m = 1,022`

Ao derivar `F_m(D)` em relação ao diâmetro `D`, obtém-se a **função densidade de probabilidade em base mássica** `f_m(D)` (denotada por `ψ_massa(D)` na página 74 da dissertação):

- **Densidade em Base Mássica**:
  `f_m(D) = dF_m(D)/dD = (m / D₆₃,₂) · (D / D₆₃,₂)^(m − 1) · exp[ −(D / D₆₃,₂)^m ]`

Fisicamente, o produto `f_m(D) · dD` já fornece diretamente a **fração da massa total inicial** de sólido contida no intervalo `[D, D + dD]`.

Por outro lado, a Equação Diferencial Parcial do Balanço Populacional (Equação 3.38 da dissertação, p. 71):
- `∂ψ(D, t)/∂t + ∂[ v(D, t) · ψ(D, t) ] / ∂D = 0`

é deduzida a partir da conservação do **número de partículas** `ψ(D, t)`. Como a massa de uma única partícula esférica de diâmetro `D` é proporcional ao seu volume (`m_p = ρ_s · (π/6) · D³ ∝ D³`), a conversão fracionária de massa `X_Zn(t)` a partir da densidade **em número** `ψ(D, t)` exige multiplicar `ψ(D, t)` por `D³` (Equação 3.49 da dissertação, p. 74):

- **Equação de Conversão do Balanço Populacional**:
  `X_Zn(t) = 1 − [ ∫ D³ · ψ(D, t) dD ] / [ ∫ D³ · ψ(D, 0) dD ]`

Na própria página 74 da dissertação, Bortot Coelho apresentou a **Equação (3.48)** (original de Herbst, 1979) que define como converter a distribuição medida em massa `ψ_massa(D)` para a distribuição em número `ψ(D)` dividindo por `D³`:

- **Equação (3.48) da Dissertação (Transformação Massa → Número)**:
  `ψ(D) = [ D⁻³ · ψ_massa(D) ] / [ ∫ D⁻³ · ψ_massa(D) dD ]`

Entretanto, nos códigos implementados nos Apêndices A2.1 (Mathematica, p. 203) e A2.3 (MATLAB, p. 205) da dissertação — e consequentemente reproduzidos nas Etapas 1.1 e 1.3 iniciais deste projeto —, a função `f_m(D)` foi inserida diretamente no lugar de `ψ(D, 0)` sem a divisão prévia por `D³`.

---

## 2. Efeito Físico da Dupla Multiplicação por D³ vs. Correção pela Divisão por D³

### 2.1. O Que Ocorria Sem Dividir por D³ (Abordagem Antiga)
Quando se utiliza `f₀(D) = f_m(D)` diretamente dentro da integral `∫ D³ · f₀(D) dD`:
1. Como `f_m(D)` já é proporcional a `D³ · f_n(D)`, o integrando no denominador torna-se:
   `D³ · f_m(D) ∝ D⁶ · f_n(D)` (sexto momento numérico!).
2. Essa ponderação espúria por `D³` desloca drasticamente a distribuição de massa que o modelo "enxerga":
   - Na distribuição real da calcina (`f_m(D)`), o pico de massa está nas partículas finas e o diâmetro médio mássico no domínio `[0,01; 297,0] μm` é **`41,6 μm`** (63,2% da massa abaixo de `41,65 μm`).
   - Já na distribuição distorcida `D³ · f_m(D)`, as partículas abaixo de `20 μm` têm seu peso quase zerado, o pico de massa é empurrado para **`~118 μm`** e o diâmetro médio efetivo salta para **`146,9 μm`**!
3. Como resultado, o modelo antigo comportava-se como se o reator tivesse sido alimentado apenas com grãos grossos (~150 μm), exigindo um encolhimento diametral acumulado muito alto (`δ = 26,31 μm`) para atingir 50% de conversão e subestimando severamente a velocidade de reação nos primeiros minutos e em polpas diluídas (`C_A0 = 0,10 mol/L`).

### 2.2. O Que Ocorre Dividindo a RRB por D³ (Nova Abordagem — Etapa 0.3)
Ao aplicar a Equação (3.48) na geração da malha granulométrica:
- `f_n(D) = [ f_m(D) / D³ ] / [ ∫_{D_min}^{D_max} (f_m(D) / D³) dD ]`

e alimentar `f₀(D) = f_n(D)` na **mesma equação de conversão** do `BatchPBMSolver`:
1. **No denominador (`t = 0`)**:
   `M₃(0) = ∫ D₀³ · f_n(D₀) dD₀ = [ 1 / I_norm ] · ∫ D₀³ · [ f_m(D₀) / D₀³ ] dD₀ = [ 1 / I_norm ] · ∫ f_m(D₀) dD₀`
   O fator `D₀³` da equação de conversão cancela exatamente o `D₀⁻³` da transformação! Assim, a distribuição de massa em `t = 0` passa a ser rigorosamente a própria RRB experimental (`r² = 0,9962` contra os 33 pontos da Tabela 5.4).
2. **No numerador (`t > 0`, após deslocamento `δ`)**:
   `M₃(δ) = ∫_δ^{D_max} (D₀ − δ)³ · f_n(D₀) dD₀ = [ 1 / I_norm ] · ∫_δ^{D_max} (1 − δ / D₀)³ · f_m(D₀) dD₀`
   Cada classe granulométrica de tamanho inicial `D₀ > δ` contribui com sua verdadeira fração mássica inicial `f_m(D₀)` multiplicada pela fração volumétrica remanescente `(1 − δ / D₀)³`.
3. **Na sensibilidade cinética `X_Zn(δ)`**:
   Para alcançar `X_Zn = 50%`, o encolhimento necessário cai de `26,31 μm` para **`4,83 μm`**, refletindo fielmente o consumo rápido da elevada população de partículas finas nos instantes iniciais da lixiviação.
