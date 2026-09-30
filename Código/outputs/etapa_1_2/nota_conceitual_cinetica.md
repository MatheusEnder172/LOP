# Nota Conceitual: O Módulo Cinético e Balanço Estequiométrico (Etapa 1.2)

**Contexto**: Este documento estabelece os fundamentos físico-químicos, termodinâmicos e matemáticos da modelagem cinética heterogênea implementada no módulo permanente [`src/physics/kinetics.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/kinetics.py). Ele detalha a velocidade de retração interfacial da partícula mineral v(D) = dD/dt, a dedução analítica do consumo de reagente por Herbst (1979) e o significado físico do parâmetro de amortecimento α proposto por Bortot Coelho (2017), demonstrando por que este termo constitui o elo ideal para a acoplagem da modelagem híbrida serial.

**Fontes bibliográficas de referência**:
- Dissertação de Mestrado: Fabrício Eduardo Bortot Coelho (PPGEM/UFMG, 2017) — *Desenvolvimento e Validação de um Modelo de Balanço Populacional para a Lixiviação de um Concentrado Ustulado de Zinco em Bancada e em Escala Piloto*, Capítulos 3, 4 e 5 (Equações 4.1, 4.2, 4.3, 3.51 e 5.3).
- Modelagem de consumo de reagente em lixiviação: Herbst, J. A. (1979) — *Rate Processes of Extractive Metallurgy*, Plenum Press.
- Reações heterogêneas fluido-sólido: Levenspiel, O. (2000) — *Engenharia das Reações Químicas*, 3ª ed., Blucher; Szekely, J. et al. (1976) — *Gas-Solid Reactions*, Academic Press.
- Relatório de testes da etapa: [`Código/outputs/etapa_1_2/relatorio_validacao_etapa_1_2.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_2/relatorio_validacao_etapa_1_2.md).

---

## 1. Do Módulo de Granulometria (Etapa 1.1) ao Módulo Cinético (Etapa 1.2)

Na **Etapa 1.1**, estruturamos a classe `RosinRammlerBennet` para descrever o estado geométrico e numérico da população de partículas sólidas em t = 0. Entretanto, um sistema particulado em suspensão lixiviante é intrinsecamente dinâmico:
- Para que o Balanço Populacional evolua no tempo, é mandatório quantificar a velocidade com que cada partícula tem seu diâmetro reduzido: a taxa linear de dissolução **v(D, t) = dD/dt**.
- Ao mesmo tempo, o ataque ácido consome prótons H⁺, reduzindo a acidez livre da fase líquida (C_Af), o que retroalimenta negativamente a taxa de dissolução.

O módulo [`src/physics/kinetics.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/kinetics.py) resolve esse acoplamento termo-cinético, fornecendo as leis de taxa que alimentarão o integrador do PBM na **Etapa 1.3**.

---

## 2. A Reação Heterogênea e a Taxa de Retração Diametral v(D)

### 2.1. Estequiometria e Mecanismo Controlador
A reação de extração de zinco a partir da zincita presente na calcina é dada por:

**ZnO_(s) + H₂SO₄_(aq) → ZnSO₄_(aq) + H₂O_(l)**

Balarini (2009) e Bortot Coelho (2017) comprovaram experimentalmente que, em rotações ≥ 840 rpm (adotou-se 1000 rpm na bancada), a resistência à transferência de massa na camada limite de líquido é minimizada ao máximo. Além disso, por não se formar uma camada espessa e insolúvel de cinzas sobre a zincita pura, a dissolução é governada estritamente pela **reação química superficial** (energia de ativação aparente E_a ≈ 13,75 kJ/mol).

### 2.2. Dedução Clássica de LeBlanc & Fogler (1987)
Para uma partícula esférica pura de diâmetro D, massa molar MM_ZnO e densidade molar ρ_s:

- **Massa da esfera**: M = ρ_s · MM_ZnO · (π/6 · D³)
- **Taxa molar de consumo**: −dn_ZnO/dt = −(1 / MM_ZnO) · (dM/dt) = −(π · ρ_s / 2) · D² · (dD/dt)

Pela lei de ação das massas para reação superficial de 1ª ordem com área externa A = π · D²:

−dn_ZnO/dt = A · k_s · C_Af = π · D² · k_s · C_Af

Igualando as duas taxas molares, obtém-se a velocidade clássica de recuo do diâmetro:

**v(D) = dD/dt = −(2 / ρ_s) · k_s · C_Af**

Onde:
- **ρ_s = 69,2 mol/L**: densidade molar de ZnO na partícula sólida;
- **k_s = 1,8 · 10⁴ μm/min**: constante cinética superficial a 30–40 °C;
- **C_Af**: Concentração molar instantânea de ácido sulfúrico livre no licor (mol/L).

---

## 3. O Termo de Amortecimento Empírico α de Bortot Coelho (2017)

### 3.1. A Limitação Físico-Química da Equação Clássica
Nos ensaios de lixiviação de calcina industrial, observou-se que a dissolução desacelera e atinge um patamar assintótico de conversão muito antes do que seria previsto pela equação clássica de primeira ordem com excesso estequiométrico (η ≥ 1). Esse fenômeno é atribuído a:
1. **Efeito do Íon Comum e Força Iônica**: A dissolução maciça de Zn²⁺ e íons sulfato SO₄²⁻ nas fases iniciais eleva drasticamente a força iônica, reduzindo o coeficiente de atividade do ácido livre.
2. **Interferência de Fases Secundárias e Ganga**: A presença de ferrita de zinco (ZnFe₂O₄), silicatos (willemita) e impurezas insolúveis cria resistências estéricas e passivação parcial da frente reativa.
3. **Consumo Concorrente de Ácido**: Dissolução incipiente de cátions secundários (Fe³⁺, Al³⁺, Ca²⁺).

### 3.2. A Modificação Cinética de Bortot Coelho (2017)
Para incorporar esse retardamento progressivo proporcional à extensão da reação, Bortot Coelho inseriu um termo de amortecimento dependente do consumo acumulado de ácido (C_A0 − C_Af):

**v(D) = dD/dt = −(2 / ρ_s) · [ k_s · C_Af − α · (C_A0 − C_Af) ]**

Onde **α** é o parâmetro de ajuste empírico (com mesma dimensão de k_s: μm/min).

### 3.3. Ponto de Parada e Conversão Teórica Máxima
Quando a reação atinge o repouso assintótico (v = 0), a força motriz líquida se anula:

k_s · C_Af* − α · (C_A0 − C_Af*) = 0  →  **C_Af* = C_A0 · [ α / (k_s + α) ]**

Substituindo C_Af* no balanço de ácido de Herbst (C_Af = C_A0 · [1 − X / η]), obtém-se analiticamente a conversão máxima assintótica (Equação 5.3 da dissertação):

**X_Zn^Max = η · [ 1 − α / (k_s + α) ]**, com restrição física **0 ≤ X_Zn^Max ≤ 1**

Para os valores nominais de bancada (k_s = 1,8 · 10⁴ μm/min e α = 5,5 · 10³ μm/min):
α / (k_s + α) = 5.500 / 23.500 ≈ 0,2340  →  [ 1 − α / (k_s + α) ] ≈ 0,7660

Isso significa que, sob α constante nominal, a reação cessa quando a acidez residual cai para 23,4% do valor inicial, limitando a conversão assintótica para η = 1,0 em cerca de **76,6%**.

---

## 4. O Balanço Estequiométrico de Herbst (1979)

Em reatores batelada sem adição contínua de reagente, o consumo de ácido sulfúrico é acoplado diretamente à conversão da espécie sólida:

**C_Af(t) = C_A0 · [ 1 − X_Zn(t) / η ]**

Onde a razão molar η pondera as quantidades iniciais de ácido e de mineral:

**η = n_A0 / n_B0 = (V · C_A0) / [ m_B0 · (T_ZnO / MM_ZnO) ]**

### 4.1. Descoberta Operacional da Pesagem de Bancada
Na análise dos 16 ensaios do Apêndice A1.1, descobriu-se que o pesquisador calibrou as massas de calcina adicionadas adotando a relação operacional simplificada de 100 g de calcina contendo exatamente 1,0 mol de ZnO (teor operacional T_ZnO = 0,8138 g/g). Com essa formulação de bancada:
**η = (40 · C_A0) / m_B0**

Com essa equação, o erro médio em relação aos níveis nominais (η = 0,5; 1,0; 1,5; 3,1) nos 16 ensaios foi de apenas **0,77%**, confirmando a precisão experimental das massas pesadas.

### 4.2. Validação com os Dados Experimentais Reais
No teste automatizado em `test_kinetics.py`, a comparação entre a previsão de Herbst e as 16 medições experimentais de acidez final residual (t = 15 min) resultou em:
- **R² = 0,9962**
- **RMSE = 0,0170 mol/L**

Esse resultado comprova que a conservação estequiométrica da fase líquida é exata e deve ser mantida inalterada como espinha dorsal mecanicista do modelo híbrido.

---

## 5. Por Que a Cinética Heterogênea é o Elo Ideal para o Modelo Híbrido Serial?

A análise das equações acima revela o ponto central de inovação do nosso projeto de LOP:

1. **A Falha do Modelo Puramente Analítico**:
   - Na dissertação original, o parâmetro α foi ajustado estaticamente em α = 5,5 · 10³ μm/min como uma constante global para tentar atender a todos os ensaios. Isso gerou desvios significativos nas condições extremas (especialmente em η = 0,5 com escassez de ácido e em η = 3,1 com grande excesso).
   - Na realidade termodinâmica, α (e consequentemente a taxa v(t)) não é uma constante: ele varia de forma não linear com C_A0, com a razão estequiométrica η, com a temperatura e ao longo do tempo de reação.
2. **A Solução via Arquitetura Serial (DDM → FPM)**:
   - Em vez de forçar um α constante ou adotar correlações empíricas rígidas, o modelo de Machine Learning (MLP, Random Forest ou SVR) é treinado para estimar dinamicamente o parâmetro cinético efetivo **α(T, C_A0, η, t)** ou diretamente a correção da taxa de retração **v(t)** a partir das condições operacionais.
   - Esse valor predito pela inteligência artificial alimenta as equações de conservação de primeiros princípios: o Balanço Populacional (para o sólido) e o balanço de Herbst (para o ácido).
   - **Resultado**: O modelo ganha a capacidade da IA de aprender o amortecimento não linear complexo do minério real, enquanto as equações mecanicistas garantem que a conservação de massa e estequiometria nunca sejam violadas (0 ≤ X_Zn ≤ 1 e C_Af ≥ 0).
