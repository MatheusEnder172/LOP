## 4.2. Metodologia de Análise Exploratória dos Dados Cinéticos de Bancada

Nesta subseção são detalhados os métodos de estruturação computacional, tratamento estatístico de dados temporais e concepção gráfica empregados na análise exploratória das trajetórias cinéticas de lixiviação descontínua em escala de bancada, a partir dos dados originais de Bortot Coelho (2017). O foco desta etapa é exclusivamente metodológico, estabelecendo como os dados foram preparados e como os padrões observados condicionam a formulação dos modelos mecanicista, orientado por dados e híbrido. A apresentação e discussão aprofundada dos resultados numéricos e dos fenômenos físico-químicos são reservadas para a Seção 5 (Resultados e Discussão).

---

### 4.2.1. Objetivos e Critérios Metodológicos da Análise Exploratória

Antes do desenvolvimento das formulações mecanicistas e dos algoritmos orientados por dados, executou-se uma etapa prévia de análise exploratória dos dados cinéticos de bancada. O objetivo metodológico dessa etapa foi triplo:

1. **Verificação de consistência e repetibilidade empírica**: Avaliar a concordância entre réplicas autênticas independentes e quantificar o erro experimental associado a cada medição temporal;
2. **Diagnóstico da sensibilidade às variáveis controladas**: Isolar e confrontar o papel da razão molar estequiométrica (η) frente à concentração inicial de ácido (C_A0) sobre a dinâmica e os limites assintóticos do sistema;
3. **Determinação dos requisitos numéricos para os modelos**: Identificar as escalas temporais e os regimes característicos de dissolução que condicionam as escolhas de malha temporal na resolução de equações diferenciais e a formulação da arquitetura híbrida serial.

---

### 4.2.2. Preparação, Limpeza e Estruturação das Trajetórias Cinéticas

A base de dados de bancada correspondente às trajetórias cinéticas de conversão de zinco foi extraída da Tabela A1.4 do Apêndice A1.1 da dissertação de Bortot Coelho (2017, p. 201). No documento original, os dados encontravam-se organizados em formato matricial horizontal, no qual os tempos de amostragem (t = 0; 0,5; 1; 2; 3; 4; 5 e 15 minutos) estavam distribuídos em colunas.

Para permitir a manipulação vetorizada e a integração com as bibliotecas numéricas em Python (McKinney, 2010), aplicou-se uma rotina de pivotamento e padronização (*tidy format*). A estrutura resultante é uma matriz relacional indexada pelas variáveis:
- Identificador do ensaio (1 a 16);
- Razão molar estequiométrica (η = 0,5; 1,0; 1,5 e 3,1);
- Concentração inicial de ácido sulfúrico (C_A0 = 0,10; 0,50; 1,00 e 1,50 mol·L⁻¹);
- Tempo de amostragem reacional (t, em min);
- Conversão fracionária de zincita (X_Zn, adimensional), obtida pela média das triplicatas.

A cada ponto amostrado foi associada a margem de incerteza estatística com 95% de confiança calculada por meio da distribuição t de Student (Equação 4.5), viabilizando a plotagem de barras de erro padronizadas.

---

### 4.2.3. Metodologia de Construção Gráfica e Visualização Comparativa

Para garantir reprodutibilidade e conformidade com os padrões de visualização científica (300 DPI), desenvolveu-se uma rotina dedicada em Python utilizando a biblioteca Matplotlib (Hunter, 2007). A concepção metodológica da representação gráfica obedeceu às seguintes diretrizes:

- **Agrupamento primário por razão molar (η)**: Os 16 ensaios foram dispostos em um painel estruturado em grade 2×2 com quatro subplots. Cada subplot reúne exclusivamente as quatro curvas cinéticas pertencentes a um único valor de η. Essa escolha metodológica fundamenta-se no princípio de que a razão molar estequiométrica atua como a variável controladora do limite termodinâmico global do reator;
- **Parametrização interna por concentração de ácido (C_A0)**: Em cada subplot, as séries temporais relativas às diferentes concentrações C_A0 foram identificadas por marcadores e cores distintas, permitindo contrastar o efeito da concentração de H₂SO₄ e da densidade de polpa para um mesmo nível estequiométrico;
- **Linhas de referência estequiométrica**: Em cada painel, sobrepôs-se uma linha horizontal tracejada representando o limite assintótico teórico máximo de conversão permitido pela disponibilidade estequiométrica de reagente (X_Zn,max = η para regimes de ácido limitante com η < 1, e X_Zn,max = 1,00 para proporção equimolar ou excesso de ácido).

A Figura 4.1 apresenta o painel gráfico resultante dessa metodologia de estruturação e visualização comparativa. A interpretação quantitativa das taxas observadas e os mecanismos de reação associados a cada curva são analisados na Seção 5 (Resultados e Discussão).

*(Inserir Figura 4.1 – Painel comparativo da análise exploratória das curvas cinéticas de conversão de zinco agrupadas por razão molar estequiométrica η e discriminadas por concentração inicial de ácido C_A0).*

*Fonte: Elaborado pelos autores a partir de dados de Bortot Coelho (2017, Apêndice A1.1, Tabela A1.4).*

---

### 4.2.4. Diagnóstico Metodológico dos Regimes de Dissolução para Modelagem

A avaliação qualitativa e a inspeção das características dinâmicas sintetizadas na Figura 4.1 permitiram estabelecer diretrizes e requisitos metodológicos inegociáveis para a formulação dos modelos matemáticos do projeto:

a) **Requisito de discretização temporal refinada na fase inicial**: A observação de que a velocidade de reação é extremamente pronunciada nos primeiros segundos de contato impõe que o integrador numérico de equações diferenciais ordinárias (ODE solver) utilize passos de tempo adaptativos ou malha temporal ultrarrefinada (Δt < 0,01 min) para t < 0,5 min. O emprego de malhas temporais uniformes e grosseiras causaria instabilidade numérica e severo erro de truncamento no Balanço Populacional;

b) **Desacoplamento entre patamar estequiométrico e taxa de reação**: O fato de que as curvas de um dado η convergem para o mesmo patamar assintótico final em t > 2 min, independentemente de C_A0, comprova metodologicamente que a conversão assintótica deve ser tratada como uma restrição de fronteira puramente estequiométrica (função direta de η), enquanto C_A0 atua como o motor cinético inicial;

c) **Justificativa estrutural para a arquitetura híbrida serial**: A desaceleração acentuada que ocorre após os instantes iniciais evidencia que um modelo fenomenológico de parâmetros estáticos (k_s e α nominais constantes) tende a divergir nas etapas tardias se apenas o consumo de reagente solúvel for computado. Esse diagnóstico justifica a estratégia híbrida adotada: o modelo mecanicista de balanço populacional (FPM) fornece a estrutura de conservação fundamental, enquanto o modelo de aprendizado de máquina (DDM) entra acoplado em série para predizer dinamicamente o fator de atenuação ou resistências residuais ao avanço da lixiviação.

---

### 4.2.5. Formalização Matemática da Restrição de Conservação de Massa (Herbst, 1979)

O acoplamento matemático rigoroso entre a conversão fracionária do sólido X_Zn(t) e a concentração de ácido sulfúrico livre remanescente na solução C_Af(t) é formalizado pela relação analítica de conservação de massa deduzida por Herbst (1979) para sistemas reacionais heterogêneos descontínuos, expressa pela Equação (4.6):

C_Af(t) = C_A0 · [ 1 - ( X_Zn(t) / η ) ]                                                               (4.6)

sendo C_Af(t) a concentração molar de ácido sulfúrico livre remanescente no instante t (mol·L⁻¹). A incorporação dessa relação analítica ao pipeline de modelagem atua como restrição física inegociável (*hard constraint*), desempenhando duas funções metodológicas indispensáveis:

1. **Garantia de não-negatividade e coerência de esgotamento**: Garante que, para ensaios operados sob deficiência estequiométrica (η ≤ 1,0), a concentração de ácido livre C_Af(t) se anule exatamente quando a conversão atingir o valor numérico de η, impedindo que os algoritmos simulem dissolução sem reagente disponível;
2. **Blindagem física do modelo híbrido**: Tanto o módulo de integração de primeiros princípios (FPM) quanto os preditores orientados por dados (DDM) são condicionados a respeitar a Equação (4.6), impedindo a ocorrência de predições fisicamente espúrias com conversões superiores a 100% ou violação de balanço de massa.

---

### 4.2.6. Critérios de Encaminhamento para as Próximas Etapas Metodológicas

A conclusão da análise exploratória dos dados cinéticos de bancada consolidou o fluxo metodológico para as subseções seguintes da Seção 4:

- Na **Subseção 4.3**, será estabelecida a metodologia de caracterização da distribuição de tamanhos das partículas do concentrado original a partir dos dados combinados de peneiramento a úmido e difração a laser (Bortot Coelho, 2017, Capítulo 5), detalhando o equacionamento, linearização e validação da função de densidade probabilística de Rosin-Rammler-Bennet (RRB) que atua como condição de contorno inicial do reator;
- Na **Subseção 4.4**, serão detalhadas as diretrizes de implementação computacional, governança de código em Python e arquitetura modular de software;
- Na **Subseção 4.5**, será formulado o modelo matemático mecanicista de primeiros princípios (FPM), abrangendo o balanço populacional unidimensional e o modelo cinético de núcleo não reagido;
- Nas **Subseções 4.6 e 4.7**, serão estabelecidos os procedimentos de treinamento e acoplamento serial com os modelos orientados por dados (DDM).
