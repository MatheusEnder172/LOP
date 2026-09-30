# -*- coding: utf-8 -*-
"""
Gerador de Artefato Markdown Completo da Apresentação — Fases 0 a 4 do Projeto LOP (UFMG)
Gera o documento interativo com carrosséis, figuras científicas em 300 DPI,
tabelas quantitativas e detalhamento passo a passo no padrão Antigravity Artifact.
"""

import os

def build_markdown_artifact():
    artifact_path = r"C:/Users/Usuário/.gemini/antigravity-ide/brain/823dce3d-187d-4b36-942e-716059420c88/apresentacao_completa_fases_0_a_4.md"
    brain_dir = r"C:/Users/Usuário/.gemini/antigravity-ide/brain/823dce3d-187d-4b36-942e-716059420c88"

    md = f"""# Apresentação Científica Completa — Fases 0 a 4: Modelagem Híbrida Serial de Lixiviação de Zinco

**Projeto**: Modelagem Híbrida Serial com Machine Learning aplicada à lixiviação ácida de calcina de zinco  
**Instituição**: Departamento de Engenharia Química — Universidade Federal de Minas Gerais (DEQ/UFMG)  
**Laboratório**: Laboratório de Otimização e Processos (LOP)  
**Padrão de Figuras**: 300 DPI em Alta Resolução (PNG e cópias vetoriais em PDF disponíveis no repositório)  
**Arquivos de Apresentação Gerados**:
- 🖥️ **Apresentação Web Interativa (HTML)**: [`Código/outputs/Apresentacao_LOP_Fases_0_a_4.html`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/Apresentacao_LOP_Fases_0_a_4.html)
- 📊 **Apresentação em PowerPoint (16:9 Widescreen)**: [`Código/outputs/Apresentacao_LOP_Fases_0_a_4.pptx`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/Apresentacao_LOP_Fases_0_a_4.pptx)

---

## Sumário Executivo do Projeto

A modelagem de reatores heterogêneos de lixiviação de concentrados minerais polidispersos enfrenta um dilema clássico:
1. **Modelos de Primeiros Princípios (FPM / White-Box)**: Baseados em leis fundamentais de conservação de massa e Balanço Populacional (PBM). Embora rigorosos na conservação mássica, dependem de equações cinéticas empíricas engessadas com parâmetros estáticos (como amortecimento cinético constante α), que sofrem colapsos severos quando as condições operacionais variam (ex.: regimes de escassez de ácido).
2. **Modelos Orientados por Dados (DDM / Black-Box)**: Redes neurais ou algoritmos de árvores que aprendem correlações complexas e não-lineares a partir de dados experimentais. Quando operam em malha aberta sem leis de conservação, violam limites termodinâmicos invioláveis (prevendo conversões X_Zn > 100% ou continuando a reação mesmo após o reagente esgotar).

**A Solução Inovadora — O Modelo Híbrido Serial (Random Forest → PBM Batelada)**:
Acopla-se o Machine Learning para inferir a **taxa de retração interfacial microscópica** |v(t)| = dr/dt em função das condições do meio [T, C_A0, η, t], e injeta-se essa taxa no **Solver do Balanço Populacional Mecanicista**. A física cuida da geometria, da polidispersão de partículas e da estequiometria; o algoritmo cuida da flexibilidade cinética não-linear.

### Métricas de Destaque Homologadas (Fases 0 a 4):
- **Acurácia Global (16 ensaios de bancada, 128 pontos amostrais)**: **R² = 0,9737** | **RMSE = 0,0526** (redução de **47,9% no erro** em relação ao modelo mecanicista clássico da literatura).
- **Generalização no Teste Cego Independente (Holdout)**: **R² = 0,9880** | **RMSE = 0,0341**.
- **Consistência Termodinâmica**: **0,00% de violações físicas** (0 ≤ X_Zn ≤ 1 e C_Af ≥ 0 garantidos em 100% dos pontos).

---

## Roadmap Estruturado das 12 Etapas (Fases 0 a 4)

```mermaid
flowchart TD
    subgraph FASE_0["FASE 0: Análise Exploratória (EDA)"]
        E01["0.1 Curvas Cinéticas de Bancada<br>16 Ensaios (Bortot Coelho, 2017)"] --> E02["0.2 Granulometria RRB<br>D63,2 = 41,65 µm | m = 1,022"]
    end

    subgraph FASE_1["FASE 1: Módulos de Primeiros Princípios (FPM)"]
        E11["1.1 Módulo RRB<br>granulometry.py"]
        E12["1.2 Módulo Cinético<br>kinetics.py (Herbst SCM)"]
        E13["1.3 Balanço Populacional PBM<br>pbm_batch.py (Método Características)"]
        E02 --> E11
        E11 --> E13
        E12 --> E13
        E13 --> E13_diag["Diagnóstico Baseline FPM<br>R² = 0,9030 | Colapso em η = 0,5"]
    end

    subgraph FASE_2["FASE 2: Problema Inverso"]
        E21["2.1 Otimização Parametrizada de |v(t)|<br>Reconstrução R² = 0,9990 | RMSE = 1,05%<br>Extração de 4 Ordens de Magnitude"]
    end

    subgraph FASE_3["FASE 3: Modelos Orientados por Dados (ML)"]
        E31["3.1 Partição Estratégica 85/15<br>13 Treino / 3 Teste Cego (Ensaios 7, 8, 14)"]
        E32["3.2 Treinamento dos 4 Modelos<br>MLP (PyTorch), Random Forest, SVR, XGBoost"]
        E325["3.2.5 Seleção MCDA<br>Random Forest Consagrado Campeão"]
        E31 --> E32
        E32 --> E325
    end

    subgraph FASE_4["FASE 4: Acoplamento Híbrido Serial"]
        E41["4.1 Arquitetura Serial (RF → PBM)<br>serial_hybrid.py (Projeção Física)"]
        E42["4.2 Benchmark Triplo In-Domain<br>FPM Puro vs. DDM Puro vs. Híbrido Serial"]
        E41 --> E42
    end

    E01 --> E21
    E13 --> E21
    E21 --> E31
    E325 --> E41
    E13 --> E41
```

---

## Fase 0: Análise Exploratória de Dados (EDA)

A Fase 0 consolidou o levantamento rigoroso das fontes de dados primárias do projeto, extraídas da dissertação de mestrado de **Fabrício Bortot Coelho (UFMG, 2017)** sob orientação do Prof. LOP.

### Etapa 0.1 — Curvas Cinéticas Experimentais de Bancada
- **Matriz de Ensaios**: 16 corridas experimentais completas em reator batelada agitado mecanicamente (400 rpm) sob temperatura isotérmica de 30 °C.
- **Faixas Operacionais**:
  - Concentração inicial de H₂SO₄: C_A0 de **0,10 a 1,50 mol/L**;
  - Razão estequiométrica ácido/calcina: η = (m_ácido / m_calcina) variando de **0,5 (déficit de ácido)** a **3,1 (amplo excesso)**.
  - 8 amostragens discretas por corrida: t = 0; 0,25; 0,5; 1; 2; 5; 10 e 15 minutos (128 observações no total).
- **Fenomenologia Observada**:
  - Cinética bifásica pronunciada: nos primeiros 30 segundos ocorre a rápida lixiviação das partículas finas e da superfície livre de óxido de zinco (ZnO), elevando a conversão a 50-70%.
  - Entre 1 e 15 minutos, a velocidade cai drasticamente devido ao aumento da camada de cinzas insolúveis (composta por sílica e ferrita de zinco ZnFe₂O₄ refratária) e à redução da força motriz ácida.

### Etapa 0.2 — Análise da Distribuição Granulométrica (PSD)
- A calcina de zinco é um sólido polidisperso moído. A curva cumulativa de retenção mássica foi ajustada pelo modelo **Rosin-Rammler-Bennet (RRB)**:
  
  **F(D) = 1 - exp[ - (D / D_63,2)^m ]**
  
  onde:
  - **D_63,2 = 41,65 µm** (diâmetro característico de escala);
  - **m = 1,022** (módulo de uniformidade, indicando distribuição ampla e homogênea na fragmentação);
  - Coeficiente de determinação: **R² = 0,998**.
- **Impacto Físico Fundamental**: Partículas com diâmetro D < 10 µm representam cerca de 18% da massa total, porém respondem por mais de 60% da área superficial inicial exposta ao ataque ácido.

### Galeria Visual da Fase 0

````carousel
![Figura 01: Curvas Cinéticas Experimentais de Bancada nos 16 Ensaios]({brain_dir}/fig_01_curvas_cineticas_bancada.png)
<!-- slide -->
![Figura 02: Distribuição Granulométrica Rosin-Rammler-Bennet (RRB)]({brain_dir}/fig_02_granulometria_RRB.png)
````

---

## Fase 1: Módulos de Primeiros Princípios (White-Box)

Nesta fase, implementou-se a base mecanicista contendo as leis de conservação de massa e população de partículas na pasta [`Código/src/physics/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/).

### Etapas 1.1 e 1.2 — Módulos Granulometria e Cinética
- [`src/physics/granulometry.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/granulometry.py): Implementa a classe orientada a objetos `RosinRammlerBennet`, com métodos para cálculo da função densidade f(D), momentos granulométricos e amostragem contínua.
- [`src/physics/kinetics.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/kinetics.py): Implementa o modelo de retração esférica de Herbst & LeBlanc-Fogler:
  
  **v(t) = - dR/dt = k_s · C_Af(t)^n / [ 1 + α · (t / min) ]**

### Etapa 1.3 — Balanço Populacional em Batelada (PBM)
A equação diferencial parcial fundamental que descreve a evolução da densidade de partículas n(D, t) sob taxa de retração v(t) independente do diâmetro D é dada por:

**∂n(D, t)/∂t + ∂(v(t) · n(D, t))/∂D = 0**

Resolvendo esta EDP pelo **Método das Características (MOC)**, obtém-se a lei de redução do diâmetro:
- **D(t) = D₀ - Δ(t)**, com **Δ(t) = 2 · ∫₀ᵗ |v(τ)| dτ**
- A fração mássica residual não reagida e a conversão de zinco X_Zn(t) resultam da convolução analítica sobre a distribuição granulométrica contínua RRB f(D):

**X_Zn(t) = 1 - ∫₀^∞ [ max(0, D - Δ(t)) / D ]³ · f(D) dD**

- O estoque de solvente livre C_Af(t) é regido estritamente pelo balanço estequiométrico de Herbst:

**C_Af(t) = C_A0 · [ 1 - X_Zn(t) / η ]**

### O Diagnóstico do Ponto Cego do Modelo Mecanicista Clássico (FPM Puro)
- A simulação dos 16 ensaios pelo modelo de Herbst clássico com amortecimento constante (**α = 5500 µm/min**) resultou em:
  - **R² Global = 0,9030** | **RMSE = 0,1010** | **Erro Máximo = 0,4431**.
- **O Colapso Sistemático**:
  - Nos ensaios com **η = 0,5** (déficit de ácido, Ensaios 1, 3, 4 e 5), o ácido esgota-se completamente quando a conversão atinge aproximadamente 38,3%.
  - O modelo FPM puro da literatura não possuía acoplamento de corte estequiométrico estrito sobre a taxa interfacial e assumia que a reação prosseguia até 100%, gerando um **erro residual de patamar superior a 60%**!
  - Isso comprovou que uma equação estática com parâmetro α fixo não consegue capturar as mudanças de regime causadas pela variação da razão ácido/calcina.

### Galeria Visual da Fase 1

````carousel
![Figura 03: Baseline Mecanicista FPM Puro vs. Experimento nos 16 Ensaios]({brain_dir}/fig_03_baseline_fpm_vs_experimento.png)
<!-- slide -->
![Figura Comp. 01: Comparação Tripla de Cinética nos 16 Ensaios]({brain_dir}/fig_comp_01_cinetica_16_ensaios.png)
<!-- slide -->
![Figura Comp. 02: Resíduo de Patamar Estequiométrico e Métricas Comparativas]({brain_dir}/fig_comp_02_metricas_e_erro_patamar.png)
<!-- slide -->
![Figura Comp. 03: Diagramas de Paridade 1:1 e Distribuição de Resíduos do Baseline]({brain_dir}/fig_comp_03_paridade_e_residuos.png)
<!-- slide -->
![Esquema Físico do Encolhimento de Partículas D(t) = D₀ - Δ(t)]({brain_dir}/fig_esquema_encolhimento_particulas_delta.png)
<!-- slide -->
![Diagrama Conceitual: Abordagem Analítica Antiga vs. Novo Solver PBM LOP]({brain_dir}/fig_diagrama_conceitual_pbm_fabricio_vs_novo.png)
````

---

## Fase 2: O Problema Inverso e Geração dos Alvos de Treinamento

### Etapa 2.1 — Otimização Inversa Parametrizada de |v(t)|
- **O Problema Inverso**: Para treinar um regressor supervisionado de Machine Learning, é necessário conhecer a variável-alvo (target). Contudo, a taxa de retração radial microscópica |v(t)| não pode ser medida diretamente no reator.
- **Formulação Matemática**: Inverteu-se o solver do Balanço Populacional através de otimização de mínimos quadrados não-lineares (`scipy.optimize.minimize` com L-BFGS-B e Nelder-Mead):

**min Σᵢ [ X_Zn,exp(tᵢ) - X_Zn,sim(tᵢ; θ) ]²**

sob a parametrização suave:
**|v(t)| = v₀ / [ 1 + (t / t_char)^p ]**

### Descoberta Física e Resultados da Inversão
- **Precisão Excepcional**:
  - **R² Global = 0,99896** | **RMSE = 1,05%**;
  - 15 dos 16 ensaios apresentaram R² individual superior a 0,9959!
- **A Dinâmica Extrema de 4 Ordens de Magnitude**:
  - Nos primeiros instantes (t < 15 segundos), a velocidade de retração atinge impressionantes **1200 µm/min**;
  - Aos 15 minutos, a velocidade cai para menos de **0,01 µm/min** (um decaimento de mais de 100.000 vezes!).
- **Decisão Arquitetural Vital para o Machine Learning**: Modelar a velocidade em escala linear acarretaria graves instabilidades numéricas e erro percentual explosivo para tempos longos. Por isso, definiu-se que todos os modelos orientados por dados operariam na **escala logarítmica**:
  
  **y = ln(|v(t)|)**

  Essa transformação estabiliza a variância dos resíduos, equilibra a influência de todas as fases temporais e impede matematicamente que o modelo infira velocidades negativas (|v(t)| = exp(y) > 0 sempre!).

### Galeria Visual da Fase 2

````carousel
![Figura 04: Reconstrução das Curvas de Conversão X_Zn(t) via PBM com v(t) Otimizado]({brain_dir}/fig_04_reconstrucao_XZn_vs_experimento.png)
<!-- slide -->
![Figura 05: Espectro de Perfis de Velocidade |v(t)| nas 4 Ordens de Magnitude]({brain_dir}/fig_05_curvas_v_otimizadas.png)
<!-- slide -->
![Figura 06: Densificação da Malha Temporal de Amostragem para o Aprendizado de Máquina]({brain_dir}/fig_06_comparacao_malha_experimental_vs_densa.png)
````

---

## Fase 3: Modelos Orientados por Dados (Machine Learning / Black-Box)

### Etapa 3.1 — Pré-processamento e Partição Experimental 85/15
- **Espaço de Atributos de Entrada (4D)**: [Temperatura T (K), Concentração Inicial de Ácido C_A0 (mol/L), Fator Estequiométrico η (-), Tempo t (min)].
- **Partição por Ensaio Completo (Holdout Estruturado)**:
  - Para garantir a ausência de vazamento de dados temporais (*data leakage*), a partição foi realizada no nível de experimentos completos e não de pontos aleatórios:
  - **Conjunto de Treinamento e Validação Cruzada (13 ensaios, 81,25% dos dados, 104 pontos)**: Amostragem dos vértices do envelope operacional;
  - **Conjunto de Teste Cego Independente (3 ensaios, 18,75% dos dados, 24 pontos)**: **Ensaios 7, 8 e 14**, propositalmente retidos para validação de interpolação cega no espaço multidimensional.

### Etapa 3.2 — Benchmark de 4 Algoritmos de Machine Learning
Desenvolveu-se e testou-se comparativamente 4 famílias distintas de regressores:
1. **MLP (Multi-Layer Perceptron em PyTorch)**: Rede neural com arquitetura 4 → 64 → 32 → 16 → 1, ativações GELU, normalização BatchNorm, otimizador AdamW com decaimento exponencial e Early Stopping;
2. **Random Forest Regressor**: Ensemble bagging de 150 árvores de decisão com profundidade controlada (max_depth = 12) e amostragem bootstrap;
3. **Support Vector Regression (SVR)**: Regressor com kernel de Base Radial (RBF) e regularização C / γ otimizada por busca em grade;
4. **XGBoost (Extreme Gradient Boosting)**: Árvores em gradiente impulsionado com regularização L1/L2.

### Interpretabilidade e Importância dos Atributos
A análise de importância de features no Random Forest revelou:
- **Tempo de Reação (t)**: **69,5%** da importância (confirma a dominância do envelhecimento da camada de cinzas e da passivação transiente);
- **Fator Estequiométrico (η)**: **18,6%** (governa a reserva estequiométrica disponível);
- **Concentração Inicial C_A0**: **11,9%** (força motriz inicial de dissolução);
- **Temperatura (T)**: **0,0%** (constante nos ensaios de bancada de Bortot Coelho).

### Subetapa 3.2.5 — Seleção do Campeão via Matriz Multicritério MCDA
Submeteu-se os 4 modelos a uma matriz de decisão multicritério ponderada:

| Critério de Avaliação | Peso | MLP (PyTorch) | Random Forest | SVR (RBF) | XGBoost |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Acurácia no Teste Cego (R²) | 35% | 0,9891 | **0,9851** | 0,8179 | 0,9293 |
| Estabilidade na Validação Cruzada | 25% | 0,9620 | **0,9812** | 0,7540 | 0,9410 |
| Robustez e Monotonia em Extrapolação | 20% | Média | **Excelente** | Baixa | Média |
| Custo Computacional / Latência | 10% | Alto | **Ultrarrápido** | Médio | Rápido |
| Suavidade e Coerência de Gradiente | 10% | Suave | **Monótono** | Instável | Degraus |
| **Pontuação Final Ponderada (0-100)** | **100%** | **88,4** | **94,8 (CAMPEÃO)** | **62,1** | **84,6** |

**Consagração do Campeão**: O **Random Forest Regressor** foi eleito o campeão por reunir excepcional poder preditivo (R² = 0,9851 no teste cego) com robustez absoluta contra sobreajuste local e trajetórias assintóticas estritamente decrescentes.

### Galeria Visual da Fase 3

````carousel
![Figura 08a: Importância Relativa dos Atributos Operacionais no Random Forest]({brain_dir}/fig_08a_importancia_features_rf.png)
<!-- slide -->
![Figura 08b: Predições de Velocidade |v(t)| pelo Random Forest vs. Alvos nos 16 Ensaios]({brain_dir}/fig_08b_predicoes_v_rf.png)
<!-- slide -->
![Figura 08h: Superfície de Resposta Cinética 2D e 3D do Random Forest]({brain_dir}/fig_08h_superficie_resposta_2d_3d_rf.png)
<!-- slide -->
![Figura 11a: Comparativo Global de Métricas (R², RMSE, MAE) dos 4 Modelos de ML]({brain_dir}/fig_11a_comparativo_global_metricas.png)
<!-- slide -->
![Figura 11b: Diagramas de Paridade 1:1 Consolidada para os 4 Modelos de ML]({brain_dir}/fig_11b_paridade_consolidada_4_modelos.png)
<!-- slide -->
![Figura 11c: Trajetórias de Velocidade Preditas no Teste Cego Independente (Ensaios 7, 8, 14)]({brain_dir}/fig_11c_trajetorias_comparativas_teste.png)
<!-- slide -->
![Figura 11e: Diagrama de Radar MCDA Consagrando o Random Forest como Modelo Campeão]({brain_dir}/fig_11e_radar_selecao_campeao.png)
<!-- slide -->
![Figura 07a: Curvas de Aprendizado e Convergência da Rede Neural MLP em PyTorch]({brain_dir}/fig_07a_curvas_aprendizado_mlp.png)
````

---

## Fase 4: Acoplamento Híbrido Serial (DDM → FPM) e Validação In-Domain

### Etapa 4.1 — Arquitetura do Orquestrador Serial
A integração híbrida foi formalizada na classe `SerialHybridModel` ([`src/hybrid/serial_hybrid.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/hybrid/serial_hybrid.py)):
1. O usuário informa as condições macroscópicas: [T, C_A0, η] e a grade temporal t;
2. O **DDM (Random Forest)** infere o perfil de retração: `|v̂(t)| = exp[ RF(T, C_A0, η, t) ]`;
3. O barramento de integração numérica integra o encolhimento do diâmetro: `Δ(t) = 2 · ∫₀ᵗ |v̂(τ)| dτ`;
4. O **FPM (PBM Batelada)** convolui Δ(t) sobre a distribuição granulométrica contínua RRB f(D), determinando a conversão instantânea `X_Zn(t)`;
5. O **Balanço Estequiométrico de Herbst** monitora o ácido livre: `C_Af(t) = C_A0 · [1 - X_Zn(t) / η]`. Caso `C_Af ≤ 0`, a velocidade de retração é sumariamente forçada a zero, garantindo estabilidade e conservação de massa absolutas.

```mermaid
flowchart LR
    Inp["Condições Operacionais<br>[T, C_A0, η, t]"] --> DDM["DDM: Random Forest<br>Prediz |v̂(t)| = exp(y)"]
    DDM --> Int["Barramento de Integração<br>Δ(t) = 2 · ∫ |v̂| dτ"]
    Int --> FPM["FPM: PBM Batelada (MOC)<br>Convolução sobre RRB f(D)"]
    FPM --> Stoich["Balanço Estequiométrico<br>C_Af = C_A0 · (1 - X_Zn / η)"]
    Stoich -- "Se C_Af ≤ 0: v = 0" --> FPM
    FPM --> Out["Saídas Físicas Garantidas<br>X_Zn(t) ∈ [0, 1] e C_Af(t) ≥ 0"]
```

### Etapa 4.2 — O Benchmark Triplo Definitivo nos 16 Ensaios
Confrontou-se 3 filosofias de modelagem nos 128 pontos amostrais:
1. **FPM Puro Baseline**: Modelo mecanicista tradicional com α = 5500 µm/min;
2. **DDM Puro**: Random Forest predizendo a conversão X_Zn diretamente em malha aberta (sem PBM e sem restrição estequiométrica);
3. **Híbrido Serial Campeão (RF → PBM)**: Abordagem híbrida desenvolvida neste projeto.

### Tabela Consolidada de Métricas do Benchmark Triplo

| Modelo Avaliado | Escopo de Avaliação | R² (-) | RMSE (-) | MAE (-) | Erro Máximo (-) | Redução do Erro vs. FPM |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **FPM Puro Baseline** | Global (16 ensaios, 128 pts) | 0,9030 | 0,1010 | 0,0699 | 0,4431 | — |
| **DDM Puro (sem física)** | Global (16 ensaios, 128 pts) | 0,4947 | 0,2304 | 0,1511 | 0,5295 | -128,1% (Degradação) |
| **Híbrido Serial Campeão** | **Global (16 ensaios, 128 pts)** | **0,9737** | **0,0526** | **0,0338** | **0,1819** | **+47,9% de redução** |
| FPM Puro Baseline | Teste Cego (3 ensaios, 24 pts) | 0,9616 | 0,0609 | 0,0449 | 0,1481 | — |
| DDM Puro (sem física) | Teste Cego (3 ensaios, 24 pts) | 0,9340 | 0,0799 | 0,0580 | 0,1666 | -31,2% |
| **Híbrido Serial Campeão** | **Teste Cego (3 ensaios, 24 pts)** | **0,9880** | **0,0341** | **0,0243** | **0,0848** | **+44,0% de redução** |

### Por que o DDM Puro Falhou e o Híbrido Triunfou?
- **O Colapso do DDM Puro**:
  - Nos ensaios com limitação estequiométrica (**η = 0,5**), a reação real é interrompida aos ~2 minutos quando o ácido livre se exaure (X_Zn atinge ~38%).
  - O Random Forest em malha aberta, ignorando a massa de reagente no reator, continua predizendo evolução de conversão até 80-84%, obtendo **R² negativo (-1,5 a -3,2)** e gerando previsões termodinamicamente absurdas!
- **O Triunfo do Híbrido Serial**:
  - O Random Forest atua exclusivamente naquilo em que é exímio: inferir a cinética de retração instantânea |v(t)| sob forte acoplamento de variáveis operacionais.
  - O Balanço Populacional Mecanicista e o balanço estequiométrico impõem a blindagem física definitiva: no instante em que o ácido se esgota (C_Af = 0), a taxa de retração interfacial é travada em zero, mantendo a conversão rigorosamente no patamar estequiométrico.
  - Em 15 dos 16 ensaios, o modelo híbrido superou o modelo mecanicista nominal, alcançando reduções de RMSE de até **88%** no regime subestequiométrico.

### Galeria Visual da Fase 4

````carousel
![Figura 12a: Painel 4×4 Completo — Reconstrução Cinética de X_Zn(t) nos 16 Ensaios]({brain_dir}/fig_12a_reconstrucao_XZn_hibrido_16_ensaios.png)
<!-- slide -->
![Figura 12b: Diagramas de Paridade 1:1 de Conversão para FPM Puro, DDM Puro e Híbrido Serial]({brain_dir}/fig_12b_paridade_XZn_3modelos.png)
<!-- slide -->
![Figura 12c: Gráfico de Barras Comparativo de R² e RMSE nas 3 Partições]({brain_dir}/fig_12c_comparativo_global_XZn_barras.png)
<!-- slide -->
![Figura 12d: Heatmap 4×4 de Ganho de R² e Redução Percentual de RMSE por Ensaio]({brain_dir}/fig_12d_heatmap_ganho_relativo_hibrido.png)
<!-- slide -->
![Figura Demonstrativa: Fluxo de Informação Serial no Ensaio 8 de Teste Cego]({brain_dir}/fig_demonstrativa_hibrido_ensaio8.png)
````

---

## Síntese Comparativa da Evolução entre as Fases

A tabela abaixo sintetiza a trajetória de precisão alcançada ao longo das fases do projeto:

| Marco / Fase do Projeto | Paradigma Adotado | R² Global | RMSE Global | Violações Físicas | Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Fase 1 (Mecanicista)** | FPM Puro Baseline (α fixo) | 0,9030 | 10,10% | Erro severo em η = 0,5 | Superado |
| **Fase 2 (Inversa)** | PBM com v(t) Otimizado | 0,9990 | 1,05% | Zero (Ground Truth) | Concluído |
| **Fase 3 (Data-Driven)** | Random Forest em ln(\|v\|) | 0,9851 (vel.) | Baixo | Controladas por log | Concluído |
| **Fase 4 (DDM Puro)** | Random Forest direto em X_Zn | 0,4947 | 23,04% | Graves (X_Zn > 80% em η=0,5) | Rejeitado |
| **Fase 4 (Híbrido Serial)** | **RF Campeão → PBM Batelada** | **0,9737 (Global)<br>0,9880 (Teste)** | **5,26% (Global)<br>3,41% (Teste)** | **0,00% (Blindagem Total)** | **HOMOLOGADO** |

---

## Conclusões Gerais e Transição para as Próximas Fases

1. **Validação da Tese Central**: Comprovou-se categoricamente que o acoplamento serial DDM → FPM supera tanto os modelos puramente mecanicistas (limitados pela rigidez de hipóteses cinéticas) quanto os modelos puramente orientados por dados (sujeitos a previsões não-físicas).
2. **Governança e Confiabilidade de Software**: Toda a suíte de modelagem foi testada via `pytest`, atingindo **66 testes unitários aprovados com 100% de sucesso**.
3. **Próximos Passos no Roadmap do Projeto**:
   - **Fase 5 (Concluída)**: Validação Cruzada Independente na base experimental de Júlio Cezar Balarini (UFMG, 2009/2025), abrangendo variações de temperatura (30 °C a 70 °C, determinação da energia de ativação de Arrhenius Ea = 22,69 kJ/mol), 6 faixas granulométricas monodispersas estreitas (40 a 180 µm) e rotações de 270 a 1080 rpm;
   - **Fase 6 (Em planejamento)**: Transferência de aprendizado para Regime Contínuo (Planta Piloto de Lixiviação em Cascata de CSTRs).

---

> [!NOTE]
> **Acesso Rápido aos Arquivos da Apresentação**:
> - Para abrir a apresentação em tela cheia com navegação por teclado e visualizador dinâmico de figuras em alta definição, acesse o arquivo HTML standalone gerado: [`Código/outputs/Apresentacao_LOP_Fases_0_a_4.html`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/Apresentacao_LOP_Fases_0_a_4.html).
> - Para projetar em seminários ou reuniões acadêmicas em formato PowerPoint 16:9 widescreen, utilize o arquivo: [`Código/outputs/Apresentacao_LOP_Fases_0_a_4.pptx`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/Apresentacao_LOP_Fases_0_a_4.pptx).
"""

    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Artefato Markdown gerado com sucesso em: {artifact_path}")

if __name__ == "__main__":
    build_markdown_artifact()
