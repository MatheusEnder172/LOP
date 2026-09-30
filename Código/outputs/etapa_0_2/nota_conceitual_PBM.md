# Nota Conceitual: O Modelo de Balanço Populacional (PBM)

**Contexto**: Este documento explica o que é o PBM, por que ele é indispensável neste projeto e como as Etapas 0.1 (cinética) e 0.2 (granulometria) se encaixam como peças de entrada do modelo.

**Fontes de referência**:
- Dissertação de Fabrício Bortot Coelho (PPGEM/UFMG, 2017), Capítulos 3 (Seção 3.5.2) e 4 (Seções 4.3 e 4.4), Equações 3.30, 3.38, 3.42, 3.45, 3.49, 3.51, 4.1, 4.2 e 4.3.
- Randolph & Larson (1988) — *Theory of Particulate Processes*.
- Ramkrishna (2000) — *Population Balances: Theory and Applications to Particulate Systems in Engineering*.
- LeBlanc & Fogler (1987) — *Population balance modeling of the dissolution of polydisperse solids*.
- Herbst (1979) — *Rate Processes of Extractive Metallurgy*.
- Balarini (2009) — Cinética de lixiviação sulfúrica do concentrado ustulado de zinco.

---

## 1. O que é o PBM?

**PBM** (*Population Balance Model*), ou **Modelo de Balanço Populacional**, é uma formulação matemática da Engenharia Química desenvolvida para descrever sistemas compostos por **populações de partículas sólidas, gotas ou bolhas**.

Em vez de tratar o sólido como uma concentração média homogênea (como se faz em cinética homogênea líquido-líquido), o PBM enxerga o reator como uma **coletividade de indivíduos**, em que cada partícula possui propriedades individuais (diâmetro, área, volume) que evoluem dinamicamente ao longo do tempo conforme a reação avança.

---

## 2. Por que um Balanço de Massa Convencional Não Funciona na Lixiviação?

Em uma reação homogênea, equacionar a taxa de consumo de reagente é direto:
`dC_A/dt = −k · C_A`.

Na **lixiviação heterogênea sólido-líquido** do concentrado de zinco, entretanto, o pó mineral é composto por bilhões de grãos com diâmetros variando desde **0,5 μm até quase 300 μm** (uma faixa de quase 3 ordens de grandeza). A modelagem com uma "partícula média" resultaria em:
- **Subestimação da velocidade inicial**: 60% das partículas têm diâmetro inferior a 38 μm (conforme confirmado na Etapa 0.2), possuem área superficial gigantesca e reagem em menos de 30 segundos.
- **Erro na conversão final**: partículas grandes demoram muito mais tempo para serem consumidas e sua dissolução lenta governa os últimos % de conversão.

O PBM resolve esse dilema: ele rastreia a **curva inteira de distribuição de tamanhos** à medida que todas as partículas vão encolhendo simultaneamente dentro do reator.

---

## 3. Analogia Intuitiva: Uma Corrida de Desgaste

Imagine uma corrida de rua com milhares de corredores de estaturas diferentes:
- Cada corredor representa uma **classe de tamanho de partícula** (*D*).
- A pista representa o **eixo do diâmetro** (*D*).
- À medida que o ácido sulfúrico reage com a superfície da partícula, ela perde massa e seu diâmetro encolhe — na analogia, o corredor caminha para trás na pista: partículas de 50 μm encolhem para 40, depois 20, até desaparecerem (diâmetro zero = dissolução completa).
- O PBM é a equação que calcula **a cada segundo quantos corredores estão em cada ponto da pista**.

---

## 4. Formulação Matemática (As Três Engrenagens Acopladas)

### 4.1. A Equação Geral do Balanço Populacional

A equação geral do balanço populacional de Randolph & Larson (Equação 3.30 da dissertação de Bortot Coelho) é:

**∂(V · ψ)/∂t = Q_E · ψ_E − Q_S · ψ_S + V · [ (B − D_pop) − ∂(v · ψ)/∂D ]**

Para o reator batelada de bancada (sem fluxo de entrada/saída, sem quebra nem aglomeração), todos os termos convectivos e de nascimento/morte anulam-se. Restando apenas:

**∂ψ(D, t)/∂t = − ∂[ v(D, t) · ψ(D, t) ] / ∂D**   (Equação 3.38)

Onde:
- **ψ(D, t)**: Densidade populacional — indica quantas partículas por unidade de volume de polpa possuem diâmetro *D* no instante *t*.
- **v(D, t) = dD/dt**: Taxa linear de dissolução — a velocidade com que o diâmetro da partícula encolhe (negativa, pois o diâmetro diminui).

Esta é uma **Equação Diferencial Parcial (EDP)** no domínio bidimensional (D × t). Para resolvê-la, são necessárias três "engrenagens" funcionando em ciclo contínuo:

### 4.2. Engrenagem 1 — Condição Inicial: f₀(D) (Etapa 0.2)

Em t = 0 min, o modelo precisa saber a distribuição de tamanhos da população de partículas que entra no reator:

**ψ(D, 0) = N(0) · f₀(D)**   (Equação 3.45)

Onde f₀(D) é a função densidade de frequência de Rosin-Rammler-Bennet validada na Etapa 0.2 com parâmetros D_63,2 = 41,65 μm e m = 1,022. Sem essa condição inicial, a EDP não pode ser resolvida.

### 4.3. Engrenagem 2 — Cinética de Encolhimento: v(D, t) (Modelo do Núcleo em Diminuição)

A taxa com que o diâmetro da partícula encolhe depende da concentração de ácido livre C_Af no licor. Balarini (2009) determinou que o mecanismo dominante é o **Núcleo em Diminuição controlado por reação química superficial**, e Bortot Coelho (2017) adicionou um parâmetro empírico α para corrigir as interações de não-idealidade:

**v(D, t) = dD/dt = − (2/ρ_s) · [ k_s · C_Af(t) − α · (C_A0 − C_Af(t)) ]**   (Equação 4.1)

Onde:
- **ρ_s = 69,2 mol/L**: Densidade molar da zincita.
- **k_s = 1,8 × 10⁴ μm/min**: Constante cinética superficial intrínseca da reação (Balarini, 2009).
- **α = 5,5 × 10³ μm/min**: Parâmetro de retardamento empírico calibrado por Bortot Coelho (2017).
- **C_Af(t)**: Concentração residual de ácido sulfúrico livre no licor no instante t.
- **C_A0**: Concentração inicial de ácido sulfúrico adicionada ao reator.

**Nota importante**: A velocidade v nesta formulação é **uniforme** — não depende do diâmetro D, apenas do tempo t (via C_Af). Isso significa que todas as partículas encolhem com a mesma velocidade linear instantânea, mas as menores desaparecem primeiro porque têm menos caminho a percorrer até D = 0.

### 4.4. Engrenagem 3 — Consumo de Ácido: C_Af(t) (Etapa 0.1)

Conforme as partículas encolhem, zinco entra em solução e ácido é consumido. A relação estequiométrica de Herbst (1979) acopla a conversão global à concentração de ácido residual:

**C_Af(t) = C_A0 · [ 1 − (X_Zn(t) / η) ]**   (Equação 3.51)

Se a razão molar for pequena (ex.: η = 0,5), C_Af(t) vai rapidamente a zero, o que anula a velocidade v(D, t) → 0 e "congela" a população de partículas, parando a reação — exatamente o comportamento observado na Etapa 0.1.

---

## 5. Como o PBM Calcula a Conversão Global (X_Zn)?

O reator não mede o diâmetro individual de cada grão; a variável monitorada é a **porcentagem mássica de zinco extraído (X_Zn)**.

Como o volume de uma partícula esférica é proporcional a D³, o volume total de sólidos no reator no instante t é dado pela integral do **terceiro momento volumétrico**:

**M₃(t) = ∫₀^∞ D³ · ψ(D, t) dD**

A conversão global é a fração de massa já dissolvida:

**X_Zn(t) = 1 − [ M₃(t) / M₃(0) ]**   (Equação 3.49)

Em palavras: integra-se o volume de todas as partículas sobreviventes no reator em cada instante e compara-se com o volume total que entrou em t = 0.

---

## 6. O Ciclo Acoplado (Diagrama de Fluxo)

O PBM não funciona "sequencialmente". As três engrenagens rodam em ciclo fechado a cada passo temporal:

```
  t = 0                                           t final
    │                                                │
    ▼                                                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                    Loop de Integração Temporal                       │
 │                                                                      │
 │  ┌──────────────────────┐                                            │
 │  │ 1. Distribuição       │  ψ(D, t)                                  │
 │  │    ψ(D, t) evolui     │─────────────┐                             │
 │  │    pela EDP (3.38)    │             ▼                             │
 │  └──────────────────────┘   ┌─────────────────────────────────────┐  │
 │            ▲                │ 2. Calcula conversão global:        │  │
 │            │ v(D,t)         │    M₃(t) = ∫ D³ · ψ(D,t) dD       │  │
 │            │                │    X_Zn(t) = 1 − M₃(t)/M₃(0)      │  │
 │  ┌─────────┴──────────────┐ └──────────────────┬──────────────────┘  │
 │  │ 4. Cinética:           │                    │ X_Zn(t)            │
 │  │    v = −(2/ρ_s) ×     │                    ▼                     │
 │  │    [k_s·C_Af − α×     │  ┌──────────────────────────────────┐    │
 │  │     (C_A0 − C_Af)]    │◀─│ 3. Consumo de Ácido (Herbst):   │    │
 │  └────────────────────────┘  │    C_Af = C_A0·[1 − X_Zn/η]    │    │
 │                              └──────────────────────────────────┘    │
 └──────────────────────────────────────────────────────────────────────┘
```

A cada passo Δt:
1. A distribuição ψ(D, t) é avançada usando a EDP com a velocidade v do passo anterior.
2. Integra-se D³·ψ para obter a conversão X_Zn(t).
3. Atualiza-se a concentração de ácido livre C_Af(t) pela equação de Herbst.
4. Recalcula-se a velocidade de encolhimento v(D, t) para o próximo passo.

---

## 7. Método Numérico de Resolução

Na dissertação original, Bortot Coelho (2017) utilizou o software Wolfram Mathematica® com o **Método Numérico das Linhas (NML)**: a EDP é semi-discretizada no espaço (eixo D) em uma malha de N pontos, transformando-a em um sistema de N equações diferenciais ordinárias (EDOs) no tempo, que são resolvidas por integradores implícitos de alta ordem.

No nosso projeto, a implementação será feita em Python usando `scipy.integrate.solve_ivp` com integrador stiff (ex.: `Radau` ou `BDF`) para resolver o sistema de EDOs equivalente, com malha de N = 1000 classes de diâmetro entre D_min = 0,01 μm e D_max = 297 μm.

---

## 8. Parâmetros Numéricos e Físicos Completos (Tabela 5.1 e 5.9 da Dissertação)

| Parâmetro | Valor | Unidade | Fonte |
| :--- | :---: | :---: | :--- |
| Constante cinética superficial (k_s) | 1,8 × 10⁴ | μm/min | Balarini (2009), Tabela 5.9 |
| Parâmetro de retardamento (α) | 5,5 × 10³ | μm/min | Bortot Coelho (2017), item 5.2.4 |
| Densidade molar da zincita (ρ_s) | 69,2 | mol/L | Tabela 5.1 |
| Massa molar do ZnO (MM_ZnO) | 81,38 | g/mol | Tabela 5.1 |
| Teor de ZnO no concentrado (T_ZnO) | 76,1 | % m/m | Tabela 5.1 |
| D_63,2 (RRB) | 41,65 | μm | Tabela 5.6 |
| m (RRB) | 1,022 | — | Tabela 5.6 |

---

## 9. Conexão com a Modelagem Híbrida (FPM + DDM)

### O que o PBM faz com perfeição (papel do FPM):
- Garante que a conservação de massa nunca seja violada.
- Respeita os limites estequiométricos (X_Zn ∈ [0, 1] e X_Zn ≤ η quando η < 1).
- Incorpora a física real de que partículas menores reagem muito mais rápido do que partículas maiores.

### Onde o PBM tradicional tem limitações (e por que precisamos de ML):
- A força iônica do licor concentrado em sulfato de zinco, a microporosidade das cinzas residuais e o ataque lento a minerais secundários (ferritas, willemita) são difíceis de descrever por equações analíticas puras.
- Bortot Coelho precisou calibrar o parâmetro empírico α manualmente para cada condição operacional.
- Na **Modelagem Híbrida**, o PBM fornece a espinha dorsal físico-química e um modelo de Machine Learning (DDM) prevê dinamicamente os parâmetros cinéticos residuais (como α), combinando a robustez da física com a flexibilidade orientada a dados.

---

## 10. Rastreabilidade das Etapas Anteriores

| Etapa | Engrenagem Alimentada | Entregável |
| :--- | :--- | :--- |
| **Etapa 0.1** (Cinética) | Engrenagem 3 — Consumo de ácido e patamares de η | Curvas X_Zn vs. t, fenômeno de colapso por C_A0 |
| **Etapa 0.2** (Granulometria) | Engrenagem 1 — Condição inicial f₀(D) e M₃(0) | Parâmetros RRB (D_63,2 = 41,65 μm, m = 1,022) |
| **Etapa 1.1** (Próxima) | Implementação computacional do PBM | Classe `RosinRammlerBennet` em Python |
