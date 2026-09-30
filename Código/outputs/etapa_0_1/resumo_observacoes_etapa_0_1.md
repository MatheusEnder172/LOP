# Análise Fenomenológica e Discussão dos Dados Cinéticos: Etapa 0.1

**Arquivo analisado**: [`Base de dados/raw/cinetica_batelada_A1_4.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Base%20de%20dados/raw/cinetica_batelada_A1_4.csv)  
**Fontes bibliográficas de referência**:
- Dissertação de Mestrado: Fabrício Eduardo Bortot Coelho (PPGEM/UFMG, 2017) — *Desenvolvimento e Validação de um Modelo de Balanço Populacional para a Lixiviação de um Concentrado Ustulado de Zinco em Bancada e em Escala Piloto*, Capítulos 3, 4 e 5 (Seções 5.2.2 e 5.2.3, Equações 3.51, 4.2 e 4.3).
- Modelagem de consumo de reagente em lixiviação: Herbst, J. A. (1979) — *Rate Processes of Extractive Metallurgy*.
- Dicionário de rastreabilidade: [`Base de dados/RASTREABILIDADE_DADOS.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Base%20de%20dados/RASTREABILIDADE_DADOS.md).

**Gráficos gerados nesta etapa**:
- Imagem de alta resolução (300 DPI): [`Código/outputs/etapa_0_1/fig_01_curvas_cineticas_bancada.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_0_1/fig_01_curvas_cineticas_bancada.png)
- Arquivo vetorial para relatórios/impressão: [`Código/outputs/etapa_0_1/fig_01_curvas_cineticas_bancada.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_0_1/fig_01_curvas_cineticas_bancada.pdf)

---

## 1. Notação: Razão Molar η (Eta) vs. Letra "N"

Nos gráficos e no plano de trabalho, o parâmetro comumente referido como **"N"** é rigorosamente a letra grega minúscula **η (eta)**. Na literatura hidrometalúrgica e no trabalho de Bortot Coelho (2017), adota-se **η** para designar a **razão molar estequiométrica** entre o agente lixiviante em solução (H₂SO₄) e o mineral reativo na matriz sólida (zincita, ZnO).

Devido à semelhança gráfica entre o traçado da letra grega η e a letra latina n (ou N), ambos os termos designam o mesmo parâmetro físico-químico no projeto.

---

## 2. Fundamentação Físico-Química e Dedução da Razão Molar (η)

### 2.1. A Reação Heterogênea de Lixiviação
O concentrado de zinco ustulado (calcina fornecida pela Nexa Resources, unidade de Três Marias - MG) contém o zinco distribuído em diferentes fases mineralógicas, sendo a predominante a **zincita (ZnO)**, que responde por cerca de **76,1% em massa** do concentrado sólido. A reação de dissolução da zincita em meio sulfúrico aquoso ocorre conforme a estequiometria 1:1:

**ZnO(s) + H₂SO₄(aq) → ZnSO₄(aq) + H₂O(l)**

Para cada 1 mol de ZnO dissolvido, é consumido estequiometricamente 1 mol de H₂SO₄.

### 2.2. Equacionamento Matemático de η
A razão molar η é calculada no instante inicial (t = 0 min) a partir da razão entre a quantidade de matéria inicial de ácido sulfúrico (reagente A) e a quantidade de matéria inicial de zincita no sólido (reagente B):

**η = n_A0 / n_B0**

Sendo:
- **n_A0 = V · C_A0**  
  Quantidade inicial de ácido sulfúrico adicionada ao reator (em mols), onde V é o volume da solução lixiviante (fixado em V = 0,400 L em todos os ensaios de bancada) e C_A0 é a concentração inicial de H₂SO₄ (mol/L).
- **n_B0 = (m_B0 · T_ZnO) / MM_ZnO**  
  Quantidade inicial de zincita contida na massa de sólido (em mols), onde m_B0 é a massa de concentrado ustulado adicionada (g), T_ZnO é a fração mássica de zincita no concentrado (T_ZnO = 0,761) e MM_ZnO é a massa molar da zincita (81,38 g/mol).

Substituindo os termos (conforme a Equação 4.3 da dissertação de Bortot Coelho, 2017):

**η = (V · C_A0) / [ (m_B0 · T_ZnO) / MM_ZnO ]**

---

## 3. Análise dos 4 Cenários de Razão Molar (η) nos Gráficos

A figura da Etapa 0.1 organiza as 16 curvas experimentais em 4 subplots de acordo com o valor de η:

### 3.1. Subplot 1: η = 0,5 (Ácido como Reagente Limitante)
- **Patamar assintótico observado**: X_Zn ≈ 0,50.
- **Mecanismo**: A quantidade de ácido carregada no reator equivale a apenas metade do necessário para reagir com toda a zincita. Em virtude da taxa de reação extremamente alta da zincita, todo o ácido sulfúrico livre é exaurido nos primeiros 30 segundos (C_Af → 0). Com isso, o pH sobe bruscamente para a faixa de 5,5 a 6,0. Conforme demonstrado nos diagramas termodinâmicos de Eh-pH (Pourbaix), em pH > 5,5 a dissolução da zincita cessa completamente por falta de força motriz ácida. Assim, a conversão final coincide com o limite estequiométrico máximo teórico:  
  **X_Zn,max = η = 0,50**.

### 3.2. Subplot 2: η = 1,0 (Proporção Estequiométrica 1:1)
- **Patamar assintótico observado**: X_Zn ≈ 0,85 a 0,87.
- **Mecanismo**: Embora haja exatamente 1 mol de H₂SO₄ para cada 1 mol de ZnO, a conversão total (1,00) não é atingida. Isso ocorre porque mais de 85% a 90% do ácido é consumido nos primeiros instantes. À medida que a concentração de ácido livre remanescente cai para valores muito próximos de zero, a velocidade de reação decresce vertiginosamente até praticamente anular-se em t > 5 min.
- **Relevância industrial**: Esta condição de η = 1,0 espelha com fidelidade a etapa de **"lixiviação neutra"** das usinas hidrometalúrgicas de zinco. Na prática industrial, opera-se com controle rigoroso de acidez para esgotar o ácido livre e permitir a hidrólise/precipitação de impurezas metálicas (como ferro e sílica), sem atacar as fases ferríticas refratárias.

### 3.3. Subplot 3: η = 1,5 (Excesso Moderado de Ácido — +50%)
- **Patamar assintótico observado**: X_Zn ≈ 0,97 a 0,98.
- **Mecanismo**: Com 50% a mais de ácido em relação ao estequiométrico, há acidez livre residual suficiente ao longo de todo o ensaio para manter a força motriz ativa, permitindo que a zincita atinja quase 100% de conversão. Os 2% a 3% não extraídos decorrem do consumo secundário de ácido por minerais acompanhantes (ferrita de zinco, willemita e calcita presentes no concentrado).

### 3.4. Subplot 4: η = 3,1 (Forte Excesso de Ácido — +210%)
- **Patamar assintótico observado**: X_Zn = 1,00 (conversão completa da zincita).
- **Mecanismo**: O ácido é adicionado em mais do que o triplo da necessidade estequiométrica da zincita. A concentração residual de ácido livre permanece elevada durante todo o tempo, o pH final mantém-se muito baixo e a zincita é dissolvida em sua totalidade. Adicionalmente, verifica-se neste caso um início de solubilização da ferrita de zinco (evidenciada pela detecção de ferro no licor, X_Fe > 0).

---

## 4. O Papel das Diferentes Concentrações Iniciais de Ácido (C_A0)

### 4.1. Significado e Valores Investigados
**C_A0** representa a concentração molar de ácido sulfúrico da solução aquosa adicionada ao reator em t = 0 min. No planejamento experimental, foram avaliados 4 patamares:
- **C_A0 = 0,10 mol/L** (aprox. 9,8 g/L de H₂SO₄ livre)
- **C_A0 = 0,50 mol/L** (aprox. 49,0 g/L de H₂SO₄ livre)
- **C_A0 = 1,00 mol/L** (aprox. 98,0 g/L de H₂SO₄ livre)
- **C_A0 = 1,50 mol/L** (aprox. 147,0 g/L de H₂SO₄ livre)

### 4.2. Vínculo entre C_A0, Massa de Sólido (m_B0) e Densidade de Polpa
Como o volume de líquido no reator era constante (V = 0,400 L), a manipulação de C_A0 para manter um dado valor fixo de η exige o ajuste proporcional da massa de concentrado adicionada:

**m_B0 = (V · C_A0 · MM_ZnO) / (η · T_ZnO)**

Portanto, variar C_A0 em um mesmo painel de razão molar significa alterar substancialmente a **razão sólido/líquido** (densidade de polpa):
- Para C_A0 = 0,10 mol/L (η = 1,0): adiciona-se apenas **m_B0 = 4,28 g** de pó mineral (polpa diluída, aprox. 10,7 g de sólido por litro).
- Para C_A0 = 1,50 mol/L (η = 1,0): adiciona-se **m_B0 = 64,16 g** de pó mineral (polpa espessa e densa, aprox. 160,4 g de sólido por litro).

### 4.3. Efeito Cinético vs. Efeito no Patamar Final
A comparação direta das quatro curvas dentro de cada quadrante do gráfico evidencia dois comportamentos distintos:
1. **Na taxa inicial (t < 0,5 min)**: Concentrações mais elevadas (1,00 e 1,50 mol/L) geram maior força motriz inicial na interface líquido-sólido, resultando em uma velocidade de dissolução ligeiramente mais acelerada nos primeiros 30 segundos.
2. **No patamar final (t > 2 min)**: **As curvas de diferentes C_A0 colapsam sobre o mesmo valor assintótico para um dado η**.
   - Ou seja, a fração final de zinco extraído independe se a reação ocorreu em polpa diluída (0,10 mol/L) ou em polpa concentrada (1,50 mol/L).
   - **Regra Fundamental**: A **razão molar η governa o patamar de conversão final**, enquanto a **concentração C_A0 atua primariamente na velocidade inicial e na densidade operacional da polpa**.

---

## 5. Relação Analítica de Consumo de Ácido (Herbst, 1979)

O acoplamento rigoroso entre a conversão do sólido X_Zn(t), a razão molar η e a concentração de ácido residual C_Af(t) é descrito pela equação clássica de Herbst (1979) para reatores batelada:

**C_Af(t) = C_A0 · [ 1 − (X_Zn(t) / η) ]**

Esta relação algébrica expressa diretamente a conservação de massa:
- Quando X_Zn(t) se aproxima de η (caso de ensaios com η ≤ 1,0), o termo entre colchetes tende a zero, fazendo com que C_Af(t) anule a força motriz química e congele a taxa de avanço da reação.
- Quando η > 1, mesmo para X_Zn = 1,00, resta uma concentração residual de ácido no licor dada por:  
  **C_Af,final = C_A0 · [ 1 − (1 / η) ] > 0**.

---

## 6. Diretrizes e Implicações para a Modelagem Híbrida

1. **Separação de Escalas Temporais**:
   - A reação apresenta duas fases bem demarcadas: uma fase ultra-rápida (t < 0,5 min), em que mais de 80% do zinco reage instantaneamente, e uma fase de desaceleração severa (t > 2 min), na qual a taxa cai ordens de grandeza.
2. **Integração no Modelo Híbrido Serial (FPM + DDM)**:
   - O modelo baseado em primeiros princípios (FPM - Balanço Populacional com Núcleo em Diminuição) deve garantir a conservação estequiométrica estrita dada pela equação de Herbst.
   - O componente orientado a dados (DDM - Machine Learning) deverá modelar as resistências dinâmicas residuais, os desvios de não-idealidade iônica e o comportamento de desaceleração assintótica que o modelo puramente analítico tem dificuldade de reproduzir sem calibração pontual empírica.
