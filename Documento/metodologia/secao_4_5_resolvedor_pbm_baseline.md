## 4.5. Metodologia de Resolução do Balanço Populacional em Batelada e Simulação Baseline FPM

Nesta subseção é descrita a metodologia analítico-numérica desenvolvida para a resolução da Equação Diferencial Parcial (EDP) do Balanço Populacional (PBM) em reatores batelada perfeitamente agitados, a formulação da redução dimensional pelo Método das Características, o algoritmo de rastreamento do encolhimento cumulativo, o acoplamento simultâneo entre as engrenagens físicas e o protocolo de simulação do modelo de referência puramente fenomenológico (*First-Principles Model* — FPM Puro). O foco desta seção é estritamente metodológico, detalhando a formulação matemática, a estrutura dos algoritmos de integração e os critérios de validação computacional. A discussão aprofundada dos resultados quantitativos de simulação, a análise de desvios em cada nível estequiométrico e os mecanismos físico-químicos associados são apresentados na Seção 5 (Resultados e Discussão).

---

### 4.5.1. Formulação da Equação Diferencial Parcial do Balanço Populacional

Em sistemas reacionais particulados homogêneos no espaço físico (reator perfeitamente misturado), a evolução temporal da densidade de distribuição de tamanhos de partículas $\psi(D, t)$ (em unidades de $\mu\text{m}^{-1}$ ou $\text{partículas}\cdot\mu\text{m}^{-1}\cdot\text{L}^{-1}$) é governada pela equação de continuidade populacional no espaço de fases (Randolph; Larson, 1988; Ramkrishna, 2000). 

Para o reator de lixiviação descontínuo em escala de bancada, a ausência de fluxos contínuos de entrada e saída de polpa ($Q_E = Q_S = 0$), combinada com a inexistência comprovada de fenômenos de aglomeração interpartículas e quebra mecânica sob as condições hidrodinâmicas operadas (Bortot Coelho, 2017), anula integralmente os termos de nascimento e morte populacional ($B = D_{\text{pop}} = 0$). Nessas condições, a formulação geral reduz-se à Equação Diferencial Parcial hiperbólica de conservação unidimensional em batelada, expressa pela Equação (4.21):

$$\frac{\partial \psi(D, t)}{\partial t} + \frac{\partial [ v(t) \cdot \psi(D, t) ]}{\partial D} = 0 \tag{4.21}$$

sujeita à condição inicial contínua em $t = 0$:

$$\psi(D, 0) = N_T(0) \cdot f_0(D)$$

sendo $N_T(0)$ o número total inicial de partículas por unidade de volume de polpa, $f_0(D)$ a função densidade de probabilidade inicial ajustada pelo modelo de Rosin-Rammler-Bennet (Equação 4.9) e $v(t) = dD/dt$ a velocidade linear de retração interfacial da partícula sólida ($\mu\text{m}\cdot\text{min}^{-1}$).

---

### 4.5.2. Redução Dimensional pelo Método das Características (MOC)

A resolução numérica direta da Equação (4.21) por métodos espaciais convencionais (diferenças finitas upwind, elementos finitos ou volumes finitos) em malhas de diâmetros fixos costuma introduzir severos erros de difusão numérica artificial, atenuando espuriamente as frentes de onda e degradando a conservação do volume total de sólidos ao longo do tempo (Ramkrishna, 2000).

No entanto, conforme estabelecido na Subseção 4.4, a velocidade de retração interfacial $v(t)$ é **espacialmente uniforme**, isto é, independe do diâmetro $D$ da partícula, dependendo unicamente da composição química instantânea da fase líquida ($C_{Af}(t)$ e $C_{A0}$). Essa propriedade física permite aplicar o Método das Características (*Method of Characteristics* — MOC) para transformar a EDP bidimensional $(D \times t)$ em um sistema desacoplado de curvas características no espaço de fases (LeBlanc; Fogler, 1987; Randolph; Larson, 1988).

As equações diferenciais que definem as curvas características no plano $(t, D)$ são formalizadas pela Equação (4.22):

$$\frac{dt}{1} = \frac{dD}{v(t)} = \frac{d\psi}{0} \tag{4.22}$$

Da Equação (4.22), decorrem duas conclusões metodológicas fundamentais:
1. Ao longo de cada curva característica, $d\psi/dt = 0$, o que comprova que o valor da função densidade populacional permanece estritamente constante;
2. Todas as partículas sólidas presentes no sistema reacional, independentemente de seu tamanho inicial, sofrem exatamente a mesma taxa linear de deslocamento ao longo do tempo.

Define-se então o **operador de encolhimento diametral linear cumulativo** $\delta(t)$ ($\mu\text{m}$), que quantifica a redução total de diâmetro acumulada desde o instante de alimentação ($t = 0$) até o tempo $t$, expresso pela Equação (4.23):

$$\delta(t) = \int_0^t - v(t')\, dt' \tag{4.23}$$

com condição inicial $\delta(0) = 0$. Como $v(t) \le 0$ para dissolução, $\delta(t)$ é uma função monótona não-decrescente do tempo ($\delta(t) \ge 0$).

A trajetória temporal característica do diâmetro de uma partícula de dimensão inicial $D_0$ no instante $t$ é dada analiticamente pela Equação (4.24):

$$D(t) = \max\left( 0,\ D_0 - \delta(t) \right) \tag{4.24}$$

A Equação (4.24) explicita o comportamento físico de encolhimento:
- Partículas com tamanho inicial superior ao encolhimento cumulativo ($D_0 > \delta(t)$) sobrevivem na suspensão com diâmetro residual $D(t) = D_0 - \delta(t)$;
- Partículas com tamanho inicial menor ou igual ao encolhimento cumulativo ($D_0 \le \delta(t)$) extinguem-se completamente da polpa por dissolução exaustiva ($D(t) = 0$).

---

### 4.5.3. Integração de Momentos Volumétricos e Mapeamento Monótono de Conversão

A evolução da fração convertida global $X_{\text{Zn}}$ decorre da variação do volume total ocupado pela população de sólidos. A partir da Equação (4.24), o terceiro momento volumétrico residual da população particulada no instante em que o encolhimento atinge o valor $\delta$, denotado por $M_3(\delta)$, é formalizado pela integral truncada da Equação (4.25):

$$M_3(\delta) = \int_{\delta}^{D_{\max}} (D_0 - \delta)^3 \cdot n(D_0, 0)\, dD_0 \tag{4.25}$$

para $\delta < D_{\max}$, e $M_3(\delta) = 0$ para $\delta \ge D_{\max}$. O limite inferior de integração em $D_0 = \delta$ expressa com exatidão que as partículas menores que $\delta$ já foram completamente dissolvidas e deixaram de contribuir para o volume da fase sólida remanescente.

A conversão fracionária de zincita $X_{\text{Zn}}(\delta)$ é calculada analiticamente pela razão entre o volume dissolvido acumulado e o volume sólido inicial ($M_3(0)$), expressa pela Equação (4.26):

$$X_{\text{Zn}}(\delta) = 1 - \frac{M_3(\delta)}{M_3(0)} = 1 - \frac{\int_{\delta}^{D_{\max}} (D_0 - \delta)^3 \cdot f_0(D_0)\, dD_0}{\int_0^{D_{\max}} D_0^3 \cdot f_0(D_0)\, dD_0} \tag{4.26}$$

A formulação da Equação (4.26) estabelece um mapeamento contínuo, analítico e estritamente monótono entre a variável cinético-espacial $\delta$ e a conversão mássica $X_{\text{Zn}}$:
1. Quando $\delta = 0$, $M_3(0) / M_3(0) = 1 \implies X_{\text{Zn}}(0) = 0$;
2. Quando $\delta \ge D_{\max}$, $M_3(\delta) = 0 \implies X_{\text{Zn}} = 1,0$;
3. A derivada $dX_{\text{Zn}}/d\delta \ge 0$ é estritamente não-negativa para todo $\delta \ge 0$, assegurando por construção matemática que o modelo fenomenológico nunca viola as leis termodinâmicas de conservação de massa ($0 \le X_{\text{Zn}} \le 1$).

Para conferir máxima eficiência computacional ao resolvedor numérico, a curva característica unidimensional $\delta \mapsto X_{\text{Zn}}(\delta)$ é pré-calculada uma única vez no início da simulação através de integração trapezoidal vetorizada de alta resolução sobre a malha de $N = 1000$ nós de diâmetros. Durante a integração temporal subsequente, a conversão é obtida por interpolação linear contínua nessa curva calibrada, eliminando a necessidade de reavaliar integrais numéricas custosas a cada passo temporal do integrador EDO.

---

### 4.5.4. Algoritmo Numérico de Integração Temporal ODE

A diferenciação da Equação (4.23) em relação ao tempo converte a EDP do Balanço Populacional em uma **única Equação Diferencial Ordinária (EDO)** escalar para a evolução temporal do encolhimento $\delta(t)$:

$$\frac{d\delta}{dt} = - v(t) = |v(t)|$$

Substituindo-se a taxa de retração interfacial (Equação 4.16) com a restrição de não-crescimento (Equação 4.20) e acoplando-se a concentração instantânea de ácido livre residual de Herbst (Equação 4.6) expressa em termos de $X_{\text{Zn}}(\delta)$, obtém-se o sistema dinâmico fechado representado pela Equação (4.27):

$$\frac{d\delta}{dt} = \frac{2}{\rho_s} \cdot \max\left( 0,\ (k_s + \alpha) \cdot C_{A0} \left[ 1 - \frac{X_{\text{Zn}}(\delta)}{\eta} \right] - \alpha \cdot C_{A0} \right) \tag{4.27}$$

com a condição de valor inicial $\delta(0) = 0$.

A resolução da Equação (4.27) foi implementada em ambiente Python por meio do resolvedor numérico de equações diferenciais ordinárias `scipy.integrate.solve_ivp`. O protocolo computacional adotou as seguintes diretrizes metodológicas:

1. **Método de integração temporal**: Empregou-se o algoritmo de Runge-Kutta explícito de ordens 4 e 5 com controle adaptativo de passo (método RK45 / Dormand-Prince). Para ensaios em que o esgotamento ultra-rápido de reagente em $t < 0,5\text{ min}$ introduz rigidez numérica (*stiffness*), o resolvedor dispõe de chaveamento automático para o método implícito de Radau de ordem 5;
2. **Critérios de tolerância numérica**: Fixaram-se tolerâncias estritas para controle do erro local de truncamento: tolerância relativa de $10^{-6}$ (`rtol=1e-6`) e tolerância absoluta de $10^{-9}$ (`atol=1e-9`), assegurando estabilidade e precisão numérica nas ordens de grandeza das micro-dimensões de encolhimento;
3. **Malha temporal de saída**: A integração é avaliada nos instantes exatos de amostragem experimental ($t = 0; 0,5; 1; 2; 3; 4; 5\text{ e } 15\text{ min}$), além de uma malha fina densa de $200$ pontos contínuos para a construção suave das curvas teóricas.

---

### 4.5.5. Protocolo de Simulação do Baseline Fenomenológico Puro (FPM)

Para consolidar o modelo de referência puramente fenomenológico (*FPM Puro*) que serve como linha de base (*baseline*) para confronto com os modelos híbridos nas etapas posteriores, simulou-se a totalidade dos 16 ensaios de lixiviação descontínua em bancada de Bortot Coelho (2017, Apêndice A1.1, Tabela A1.4).

A parametrização do baseline FPM fixou rigorosamente os valores nominais estabelecidos na literatura acadêmica de referência, sem qualquer calibração empírica ajustada caso a caso:
- Constante cinética intrínseca superficial: $k_s = 1,8 \times 10^4\ \mu\text{m}\cdot\text{min}^{-1}$ (Balarini, 2009);
- Parâmetro de amortecimento nominal constante: $\alpha_{\text{nominal}} = 5,5 \times 10^3\ \mu\text{m}\cdot\text{min}^{-1}$ (Bortot Coelho, 2017);
- Densidade molar da zincita: $\rho_s = 69,2\ \text{mol}\cdot\text{L}^{-1}$;
- Distribuição granulométrica inicial: modelo RRB com $D'_{63,2} = 41,65\ \mu\text{m}$ e $m = 1,022$.

A Figura 4.3 ilustra o painel comparativo multiescalar das trajetórias cinéticas experimentais de conversão de zinco sobrepostas às trajetórias simuladas pelo baseline FPM Puro para as 16 condições operacionais de bancada.

A quantificação da acurácia e a avaliação dos resíduos entre as predições do modelo mecanicista e os dados experimentais foram padronizadas com base nas três métricas estatísticas formais definidas a seguir:

1. **Raiz do Erro Quadrático Médio (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N_{\text{pts}}} \sum_{i=1}^{N_{\text{pts}}} \left( X_{\text{exp},i} - X_{\text{calc},i} \right)^2} \tag{4.28}$$
2. **Erro Médio Absoluto (MAE)**:
   $$\text{MAE} = \frac{1}{N_{\text{pts}}} \sum_{i=1}^{N_{\text{pts}}} | X_{\text{exp},i} - X_{\text{calc},i} | \tag{4.29}$$
3. **Coeficiente de Determinação ($R^2$)**:
   $$R^2 = 1 - \frac{\sum_{i=1}^{N_{\text{pts}}} \left( X_{\text{exp},i} - X_{\text{calc},i} \right)^2}{\sum_{i=1}^{N_{\text{pts}}} \left( X_{\text{exp},i} - \bar{X}_{\text{exp}} \right)^2} \tag{4.30}$$

sendo $X_{\text{exp},i}$ a conversão experimental observada na triplicata de bancada, $X_{\text{calc},i}$ o valor calculado pelo modelo fenomenológico, $\bar{X}_{\text{exp}}$ a média global das medições experimentais e $N_{\text{pts}}$ o número total de observações avaliadas.

Os valores numéricos de $R^2$, RMSE e MAE obtidos para cada ensaio, a análise detalhada das discrepâncias nos diferentes regimes estequiométricos e a fundamentação físico-química dos desvios observados são apresentados e discutidos na Seção 5 (Resultados e Discussão).

*(Inserir Figura 4.3 – Painel comparativo das curvas cinéticas de conversão de zinco simuladas pelo modelo mecanicista de primeiros princípios FPM puro frente aos dados experimentais de bancada de Bortot Coelho (2017)).*

*Fonte: Elaborado pelos autores a partir de dados de Bortot Coelho (2017, Apêndice A1.1, Tabela A1.4).*
