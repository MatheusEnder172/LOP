# Nota Conceitual: O Módulo de Granulometria (Etapa 1.1)

**Contexto**: Este documento apresenta os fundamentos físico-químicos, a formulação matemática e os detalhes de engenharia de software da implementação permanente do módulo de distribuição granulométrica Rosin-Rammler-Bennet (`src/physics/granulometry.py`). Ele explica como a distribuição de tamanhos de partícula atua como a condição de contorno inicial indispensável para a conservação de massa no Modelo de Balanço Populacional (PBM) e nos modelos híbridos subsequentes.

**Fontes de referência**:
- Dissertação de Fabrício Bortot Coelho (PPGEM/UFMG, 2017), Seções 3.5.1, 4.3, 5.1.2 e Tabela 5.9.
- Rosin, P.; Rammler, E. (1933) — *The Laws Governing the Fineness of Powdered Coal*. Journal of the Institute of Fuel, 7, 29-36.
- Randolph, A. D.; Larson, M. A. (1988) — *Theory of Particulate Processes*. Academic Press.
- LeBlanc, S. E.; Fogler, H. S. (1987) — *Population balance modeling of the dissolution of polydisperse solids*. AIChE Journal, 33(1), 54-63.
- Relatório de testes da etapa: [`Código/outputs/etapa_1_1/relatorio_validacao_etapa_1_1.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_1/relatorio_validacao_etapa_1_1.md).

---

## 1. Do Script Exploratório ao Módulo Permanente de Primeiros Princípios

Na **Etapa 0.2**, o objetivo foi estritamente investigativo: carregar a tabela `granulometria_RRB.csv`, plotar as curvas de calibração em 4 painéis e confirmar se os parâmetros ajustados por Bortot Coelho (D₆₃,₂ = 41,65 μm e m = 1,022) tinham aderência estatística aos dados de bancada da calcina da Nexa Resources.

Concluída a validação visual e estatística, surgiu uma necessidade arquitetural crítica de Engenharia de Software:
- **Scripts exploratórios não são reutilizáveis**: Eles realizam operações sequenciais voltadas a gerar figuras, mas não podem ser instanciados de forma limpa e rápida por solvers de equações diferenciais ordinárias (ODEs) ou diferenciais parciais (PDEs).
- **Necessidade de Encapsulamento**: O resolvedor do Balanço Populacional (Etapa 1.3) e as redes neurais híbridas (Etapas 2 e 3) precisam consultar continuamente a densidade de partículas, gerar malhas espaciais discretizadas e integrar momentos de volume em tempo de execução.

Na **Etapa 1.1**, criou-se a classe `RosinRammlerBennet` dentro do pacote permanente [`src/physics/granulometry.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/granulometry.py). Esse componente foi desenhado seguindo os princípios de responsabilidade única (SOLID), com tipagem estática completa, verificação de limites assintóticos e independência de dependências externas desnecessárias.

---

## 2. Fundamentação Matemática de Rosin-Rammler-Bennet (RRB)

### 2.1. A Equação Cumulativa Passante F(D)

A distribuição de Rosin-Rammler (equivalente à distribuição estatística de Weibull aplicada a sistemas particulados) descreve a probabilidade cumulativa mássica de uma partícula possuir diâmetro inferior ou igual a *D*:

**F(D) = 1 − exp[ − (D / D₆₃,₂)^m ]**

Onde:
- **D**: Diâmetro característico da partícula (em μm).
- **D₆₃,₂ = 41,65 μm**: Diâmetro característico de retenção/passante. Fisicamente, corresponde ao diâmetro para o qual exatamente 63,21% da massa total do pó já passou pela malha. Esse valor decorre analiticamente de:
  F(D₆₃,₂) = 1 − exp(−1) = 1 − 0,367879 = 0,632121 (63,21%).
- **m = 1,022**: Módulo de dispersão ou coeficiente de uniformidade.
  - Se m fosse muito alto (ex.: m > 4), a distribuição seria quase monodispersa (partículas praticamente do mesmo tamanho).
  - Como m ≈ 1,0, a distribuição aproxima-se de um decaimento exponencial puro [1 − exp(−D / D_médio)], o que traduz a realidade de concentrados ustulados industriais: uma **população extremamente polidispersa**, com uma fração massiva de partículas ultrafinas (abaixo de 10 μm) convivendo com grãos relativamente grosseiros (acima de 100 μm).

### 2.2. A Função Densidade de Probabilidade Mássica f₀(D)

Ao derivar analiticamente F(D) em relação a *D*, obtém-se a função densidade de probabilidade inicial (base mássica), que expressa a fração de massa existente por unidade infinitesimal de diâmetro dD:

**f₀(D) = dF/dD = (m / D₆₃,₂) · (D / D₆₃,₂)^(m − 1) · exp[ − (D / D₆₃,₂)^m ]**

Essa função f₀(D) é a **condição inicial espacial** que alimenta a equação diferencial parcial do PBM em t = 0.

---

## 3. Teoria dos Momentos Estatísticos e a Função Gama

Uma das vantagens mais expressivas de adotar analiticamente o modelo RRB em vez de usar interpolações numéricas brutas de dados de peneiramento é a existência de soluções analíticas fechadas para todos os seus momentos estatísticos.

O k-ésimo momento de uma distribuição f₀(D) é formalmente definido como:

**M_k = E[D^k] = ∫₀^∞ D^k · f₀(D) dD**

Substituindo a expressão analítica de f₀(D) e aplicando a substituição de variável u = (D / D₆₃,₂)^m, a integral transforma-se diretamente na definição da **Função Gama de Euler**:

**M_k = (D₆₃,₂)^k · Γ(1 + k/m)**

Onde Γ(z) = ∫₀^∞ u^(z−1) · exp(−u) du.

### 3.1. Significado Físico das Ordens dos Momentos

| Ordem (k) | Notação | Expressão Analítica | Valor para a Calcina | Significado Físico no Processo |
| :---: | :---: | :---: | :---: | :--- |
| **0** | M₀ | Γ(1) = 1,0 | 1,0000 | **Conservação da Massa Total**: A área total sob a curva de densidade mássica é exatamente 1 (100%). |
| **1** | M₁ (μ) | D₆₃,₂ · Γ(1 + 1/m) | **41,28 μm** | **Diâmetro Médio Mássico**: Centro de gravidade da distribuição. Reproduz com exatidão a pág. 133 de Bortot Coelho. |
| **2** | M₂ | (D₆₃,₂)² · Γ(1 + 2/m) | 3.396,9 μm² | **Área Superficial Específica**: Proporcional à área inicial de contato sólido-líquido disponível para o ataque do ácido. |
| **3** | M₃ | (D₆₃,₂)³ · Γ(1 + 3/m) | **399.968,0 μm³** | **Volume das Partículas**: Proporcional ao volume e à massa inicial de sólido mineral alimentado no reator. |

A partir dos momentos M₁ e M₂, calcula-se também a variância σ² = M₂ − (M₁)² e o **Coeficiente de Variação (CV)**:
**CV = σ / μ = 0,98**
Esse valor de CV próximo a 1,0 comprova quantitativamente a elevadíssima dispersão granulométrica do minério.

---

## 4. O Terceiro Momento (M₃) como Âncora da Conservação de Massa no PBM

Por que o terceiro momento (M₃) recebeu tanta atenção nos testes da Etapa 1.1?

No Modelo de Balanço Populacional, a população de partículas é descrita por sua densidade populacional ψ(D, t). O volume total ocupado pelas partículas sólidas por unidade de volume de suspensão em qualquer instante *t* é dado pela integral cúbica de seus diâmetros:

**V_sólido(t) = k_v · ∫₀^∞ D³ · ψ(D, t) dD = k_v · M₃(t)**

Onde k_v é o fator volumétrico de forma (para esferas perfeitas, k_v = π / 6).

Como a densidade mássica do sólido (ρ_s) e a estequiometria do mineral são constantes durante o avanço reativo, a **conversão fracionária de zinco X_Zn(t)** é obtida diretamente pelo balanço volumétrico:

**1 − X_Zn(t) = V_sólido(t) / V_sólido(0) = M₃(t) / M₃(0)**

Portanto:
**X_Zn(t) = 1 − [ M₃(t) / M₃(0) ]**

Essa relação demonstra uma verdade fundamental da física do processo:
> **Se o cálculo do terceiro momento inicial M₃(0) contiver imprecisões numéricas ou descontinuidades de malha, todo o cálculo da conversão química X_Zn(t) ao longo de todo o tempo da batelada estará corrompido.**

---

## 5. Discretização Numérica da Malha e Análise de Truncamento

Em um computador, os resolvedores numéricos de equações diferenciais parciais (como o método das linhas com diferenças finitas ascendentes) não integram funções em domínios contínuos infinitos [0, ∞). Eles exigem uma **malha discreta de nós espaciais** {D₀, D₁, ..., D_N}.

A classe `RosinRammlerBennet.generate_mesh()` resolve essa ponte definindo:
- **Faixa de Diâmetros**: D_min = 0,01 μm até D_max = 297,0 μm.
- **Resolução Espacial**: N = 1500 nós lineares uniformemente espaçados (ΔD ≈ 0,198 μm).

Dois testes rigorosos foram executados no script de validação (`test_granulometry.py`):

### 5.1. Efeito do Truncamento Físico da Cauda Superior
A integral teórica contínua do terceiro momento de zero a infinito resulta em:
**M₃_infinito = 399.968,03 μm³**

No entanto, no minério real submetido à lixiviação, as partículas passaram previamente por uma malha de peneiramento industrial que remove frações grosseiras. O diâmetro máximo experimental medido por difração a laser foi de 297,0 μm. Integrando analiticamente apenas no domínio físico real [0,01; 297,0] μm:
**M₃_físico_referência = 376.877,38 μm³ (94,2% do valor infinito)**

Os 5,8% restantes correspondem à cauda assintótica infinita do modelo matemático de Weibull, a qual não possui contrapartida física no pó de calcina real.

### 5.2. Erro de Integração Numérica na Malha
Calculando o terceiro momento na malha discreta de 1500 nós pela Regra dos Trapézios composta:
**M₃_numérico = 376.877,36 μm³**

Comparando o valor numérico com a quadratura adaptativa de alta precisão (SciPy `quad`):
**Erro Relativo = |376.877,36 − 376.877,38| / 376.877,38 = 0,000005%**

Um erro de apenas 5 partes em 100 milhões garante que a discretização de 1500 nós é uma representação de fidelidade absoluta, eliminando qualquer viés numérico artificial de dissipação de massa.

---

## 6. Síntese dos Resultados e Métricas da Etapa 1.1

A tabela a seguir consolida o laudo técnico de validação do módulo:

| Teste / Métrica | Referência Teórica / Experimental | Calculado pela Classe `RosinRammlerBennet` | Status |
| :--- | :---: | :---: | :---: |
| **Limite F(0)** | 0,0000 | 0,0000 | Aprovado |
| **Limite F(D₆₃,₂)** | 1 − e^(−1) = 0,63212 | 0,63212 | Aprovado |
| **Limite F(10.000 μm)** | 1,0000 | 1,0000 | Aprovado |
| **Diâmetro Médio (M₁)** | 41,28 μm (Dissertação, p. 133) | 41,28 μm | Aprovado |
| **Coeficiente de Variação (CV)** | 0,9700 (Tabela 5.9) | 0,9785 | Aprovado |
| **Erro da Malha Discreta em M₃(0)** | < 0,0001% (Tolerância) | **0,000005%** | Aprovado |
| **R² contra Dados Reais** | > 0,9900 | **0,9962** | Aprovado |
| **RMSE contra Dados Reais** | < 0,0500 | **0,0210** | Aprovado |
| **MAE contra Dados Reais** | < 0,0500 | **0,0142** | Aprovado |

---

## 7. Como Este Módulo Alimenta as Próximas Etapas

O módulo [`src/physics/granulometry.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/granulometry.py) agora é um alicerce permanente do repositório, servindo como ponto de partida para os seguintes módulos:

1. **Etapa 1.2 (Módulo Cinético - `src/physics/kinetics.py`)**:
   - A velocidade de retração interfacial da partícula v(D, t) = dD/dt e o consumo estequiométrico de ácido dependem da área e diâmetro de cada nó de partícula fornecido pela malha gerada por `generate_mesh()`.
2. **Etapa 1.3 (Resolvedor do PBM em Batelada - `src/physics/pbm_solver.py`)**:
   - A condição inicial de partículas no reator será diretamente o vetor `f0_mesh`, e a conversão de zinco X_Zn(t) usará a base `m3_numerical` para computar a perda volumétrica exata a cada passo de integração de Runge-Kutta.
3. **Etapas 2 e 3 (Modelagem Híbrida Serial, Paralela e KAH)**:
   - Os modelos de Machine Learning (MLP, Random Forest) preverão correções dinâmicas para a taxa de reação k_app ou para o resíduo da cinética, mas **a física da conservação granulométrica continuará estritamente governada pela classe `RosinRammlerBennet`**, assegurando que os limites físicos da conservação de massa nunca sejam violados.
