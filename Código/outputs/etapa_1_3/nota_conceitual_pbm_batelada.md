# Nota Conceitual: Balanço Populacional em Batelada e Resolução pelo Método das Características

**Etapa**: 1.3 — Resolvedor PBM Batelada e Simulação Baseline FPM Puro  
**Objetivo**: Fundamentar matematicamente a redução da Equação do Balanço Populacional (PBM) a uma EDO ordinária via Método das Características, detalhar a integração de momentos de volume e analisar as limitações físicas do modelo puramente fenomenológico.

---

## 1. A Equação Geral do Balanço Populacional (PBM)

Em um reator batelada perfeitamente agitado, a dinâmica temporal da função densidade de distribuição de tamanhos de partículas f(D, t) (em μm⁻¹ ou partículas/(μm·L)) na ausência de quebra (*breakage*) e de aglomeração (*agglomeration*) é regida pela equação de continuidade no espaço de fases de tamanho (Randolph & Larson, 1988):

**∂f(D, t)/∂t + ∂[ v(D, t) · f(D, t) ] / ∂D = 0**

Onde:
- **D**: Dimensão característica linear da partícula mineral (μm).
- **t**: Tempo de reação (min).
- **v(D, t) = dD/dt**: Taxa linear de crescimento ou retração diametral da partícula (μm/min). Na lixiviação dissolutiva, v ≤ 0.

---

## 2. Redução da EDP pelo Método das Características

A resolução numérica direta da equação acima como uma Equação Diferencial Parcial (EDP) hiperbólica tradicional por diferenças finitas ou volumes finitos costuma introduzir **dispersão numérica artificial** e oscilações nas frentes de onda de partículas finas.

No entanto, para a lixiviação de calcina de zinco (zincita ZnO), a etapa determinante comprovada experimentalmente é a **reação química heterogênea na interface sólido-líquido**, sem formação de camada difusiva de cinzas aderente (Bortot Coelho, 2017; LeBlanc & Fogler, 1987).

Essa condição termodinâmica garante que a velocidade de retração interfacial v **não depende do diâmetro D da partícula**:

**v(D, t) = v(t)   para todo D**

### 2.1. Traçado das Curvas Características
Pela regra da cadeia, a derivada total ao longo de uma trajetória característica no plano (t, D) é:

df/dt = ∂f/∂t + (dD/dt) · (∂f/∂D) = ∂f/∂t + v(t) · (∂f/∂D) = − f · [∂v(t)/∂D] = 0

Isso estabelece duas conclusões fundamentais:
1. **A densidade populacional f permanece constante** ao longo de cada curva característica.
2. Cada partícula de tamanho inicial D₀ no instante t = 0 sofre uma retração idêntica ao longo do tempo:

**D(t) = D₀ − δ(t)**

Onde **δ(t)** é o **deslocamento diametral acumulado** (linear shrinkage):

**δ(t) = ∫₀^t |v(τ)| dτ ≥ 0,   com δ(0) = 0**

### 2.2. A EDO Reduzida do Sistema
Diferenciando δ(t) em relação ao tempo, a EDP original reduz-se a uma **única Equação Diferencial Ordinária (EDO)** escalar:

**dδ/dt = |v(t)| = −v(t) ≥ 0**

Esta simplificação analítica é de valor inestimável: ela converte um problema complexo de EDP bidimensional em uma EDO unidimensional de velocidade de cálculo em milissegundos e estabilidade numérica absoluta.

---

## 3. Preservação de Momentos e Cálculo da Conversão Mássica

No início do processo (t = 0), a população particulada possui densidade volumétrica f₀(D₀) descrita pela distribuição Rosin-Rammler-Bennet (RRB). O volume total inicial ocupado pela população (terceiro momento volumétrico M₃(0)) no domínio experimental [D_min, D_max] é:

**M₃(0) = ∫ D₀³ · f₀(D₀) dD₀**

À medida que o tempo avança e o encolhimento δ(t) se acumula:
- Todas as partículas com tamanho inicial D₀ ≤ δ(t) extinguem-se por dissolução completa (D = 0).
- As partículas sobreviventes (D₀ > δ(t)) encolhem para D(t) = D₀ − δ(t).

Portanto, o terceiro momento residual no instante t é dado por:

**M₃(δ) = ∫_δ^D_max (D₀ − δ)³ · f₀(D₀) dD₀**,   se δ < D_max  (e 0 se δ ≥ D_max)

A conversão mássica ou volumétrica de zinco X_Zn(t) é dada rigorosamente pela razão de volumes consumidos:

**X_Zn(t) = 1 − [ M₃(δ(t)) / M₃(0) ]**

Como a função M₃(δ) é monotonicamente decrescente em relação a δ, a função X_Zn(δ) é **estritamente crescente e confinada no intervalo físico [0, 1]**, garantindo o princípio inegociável de conservação de massa.

---

## 4. O Sistema Acoplado Fechado (As Três Engrenagens)

O sistema de equações que governa o reator batelada fecha-se através do acoplamento contínuo entre as três engrenagens físicas fundamentais:

```
                      ┌──────────────────────────────────────────────┐
                      │    1. BALANÇO POPULACIONAL (PBM)             │
                      │    dδ/dt = |v(t)|  -->  X_Zn = 1 - M3(δ)/M3(0)│
                      └──────────────────────┬───────────────────────┘
                                             │ X_Zn(t)
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    2. BALANÇO ESTEQUIOMÉTRICO (HERBST)       │
                      │    C_Af(t) = C_A0 · [1 - X_Zn(t) / η]        │
                      └──────────────────────┬───────────────────────┘
                                             │ C_Af(t)
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    3. CINÉTICA INTERFACIAL                   │
                      │    v(t) = -(2/ρ_s)·[ks·C_Af - α·(C_A0-C_Af)] │
                      └──────────────────────┬───────────────────────┘
                                             │ v(t)
                                             └─────────► Retorna ao PBM
```

---

## 5. Por que o Modelo Fenomenológico Puro (FPM) Falha?
### A Justificativa Epistemológica da Modelagem Híbrida Serial

A simulação dos 16 ensaios de bancada com o FPM nominal puro obteve um desempenho global de **R² = 0,9030** e **RMSE = 0,1010** (10,1% de erro médio quadrático).

Embora qualitativamente coerente, a análise detalhada dos 16 ensaios expõe limitações intrínsecas da abordagem mecanicista pura com parâmetros estáticos:

1. **A Hipótese Falha de α Constante**:
   - Bortot Coelho adotou α_nominal = 5.500 μm/min fixo para todos os ensaios.
   - Porém, o termo de amortecimento físico-químico real agrega efeitos altamente não-lineares:
     - Formação de micropelículas viscosas ou passivação interfacial por ferritas de zinco (ZnFe₂O₄) e silicatos.
     - Aumento massivo da força iônica da solução pela liberação rápida de Zn²⁺ e SO₄²⁻.
     - Variação do coeficiente de atividade iônica do ácido livre.
   - Como consequência, o modelo estático **subestima gravemente a conversão em baixas razões molares**:
     - Em η = 0,5: O experimento real esgota o ácido e atinge X_Zn = 0,5000, mas o FPM nominal estaciona prematuramente em 0,3830 (erro absoluto de 11,7%).
     - Em η = 1,0: O experimento real atinge X_Zn ≈ 0,85 a 0,87, mas o FPM nominal para em 0,7660 (erro de ~10%).

2. **Divergência Cinética em Suspensões Diluídas (C_A0 = 0,10 mol/L)**:
   - Para C_A0 = 0,10 mol/L, a densidade de sólidos cai para apenas 3 a 20 g/L (polpa ultradiluída).
   - O cisalhamento hidrodinâmico proporcionado pela rotação de 1000 rpm maximiza a transferência de massa convectiva, acelerando a extração inicial nos primeiros 30 segundos muito além do que uma cinética interfacial padrão com k_s constante é capaz de prever (R² caindo para 0,53 - 0,76).

### A Solução: Arquitetura Serial Híbrida (DDM → FPM)
Esse diagnóstico experimental valida com precisão cirúrgica a hipótese central do projeto:

- **O que a física faz com perfeição (White-Box)**:
  - O Balanço Populacional unidimensional dδ/dt = |v(t)|.
  - A preservação da geometria polidispersa do sólido via M₃(δ).
  - A conservação estequiométrica do reagente na fase líquida via balanço de Herbst (1979).
  - A garantia inquebrantável de que a conversão sempre pertence a [0, 1] e a acidez C_Af ≥ 0.
- **O que a Inteligência Artificial deve assumir (Black-Box)**:
  - Substituir o termo empírico rígido com α constante por um modelo de Machine Learning treinado para estimar a taxa dinâmica de retração **v(t)** (ou uma função adaptativa **α(T, C_A0, η, t)**) diretamente das condições de processo.
- **Benefício**: Unir a precisão de dados e flexibilidade não-linear do Machine Learning com a robustez e interpretabilidade inegociáveis dos primeiros princípios.
