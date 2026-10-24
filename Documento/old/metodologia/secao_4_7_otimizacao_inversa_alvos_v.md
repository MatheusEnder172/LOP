## 4.7. Metodologia de Otimização Inversa e Determinação dos Alvos Cinéticos de Dissolução

Nesta subseção é descrita a metodologia analítico-computacional concebida para contornar a impossibilidade de medição pontual direta da taxa de retração interfacial $|v(t)|$ em reatores heterogêneos polidispersos. Detalham-se a formulação do problema inverso acoplado ao Balanço Populacional, a parametrização contínua bi-exponencial regularizada, a solução analítica exata da integral do deslocamento cumulativo $\delta(t)$, o algoritmo de minimização não-linear quase-Newton (L-BFGS-B) com múltiplos pontos de partida (*multi-start*) e a geração estruturada das bases de dados supervisionadas que alimentam os algoritmos de aprendizado de máquinas.

---

### 4.7.1. A Problemática Inversa na Lixiviação de Populações Polidispersas

Na arquitetura de modelagem híbrida serial proposta para o processo de lixiviação de zinco (detalhada nas Subseções 4.9 e 4.10), o regressor de aprendizado de máquinas (*Data-Driven Model* — DDM) não visa prever diretamente a conversão mássica final $X_{\text{Zn}}(t)$. O papel da inteligência artificial no acoplamento é atuar como uma lei constitutiva flexível orientada por dados, inferindo a grandeza fenomenológica intermediária fundamental: a velocidade linear de retração de diâmetro de partícula, expressa em módulo por:

$$|v(t)| = \left| \frac{dD}{dt} \right| = - \frac{dD}{dt} \ge 0 \quad (\mu\text{m}\cdot\text{min}^{-1})$$

Entretanto, em suspensões particuladas industriais ou de bancada sob intensa agitação mecânica (400 rpm), é fisicamente inviável medir a derivada temporal do diâmetro $dD/dt$ de partículas micrométricas individuais em tempo real. As grandezas experimentais efetivamente monitoradas ao longo do tempo nos 16 ensaios de bancada limitam-se à concentração de zinco solubilizado no licor e, por estequiometria, à conversão fracionária global de zincita $X_{\text{Zn}}(t)$, obtida em 8 instantes discretos ($t \in \{0; 0,5; 1,0; 2,0; 3,0; 6,0; 10,0; 15,0\}\ \text{min}$).

Para obter os valores de referência (*ground truth*) de $|v(t)|$ necessários para o treinamento supervisionado dos modelos de regressão, foi mandatório formular e resolver um **problema inverso de otimização dinâmica** (Tarantola, 2005; Aster; Borchers; Thurber, 2018): determinar qual trajetória temporal de retração $|v(t)|$, quando integrada e convoluída com a distribuição granulométrica contínua inicial de Rosin-Rammler-Bennet pelo resolvedor mecanicista `BatchPBMSolver` (Subseção 4.5), reproduz com máxima fidelidade os perfis experimentais de conversão observados.

---

### 4.7.2. Parametrização Bi-Exponencial Regularizada da Cinética Interfacial

A taxa de dissolução de partículas de calcina de zinco exibe duas escalas temporais acentuadamente distintas durante o ensaio em batelada:
1. Um transiente inicial ultrarrápido ($t < 0,5\ \text{min}$), caracterizado por elevadíssima taxa de retração interfacial devido à abundância de sítios ativos rugosos na superfície externa e à máxima concentração de ácido livre ($C_{A0}$);
2. Uma desaceleração progressiva intermediária ($0,5 \le t \le 6,0\ \text{min}$), decorrente da suavização superficial das partículas e do consumo contínuo do reagente lixiviante;
3. Uma atenuação assintótica suave em tempos longos ($t > 6,0\ \text{min}$), onde a taxa aproxima-se de zero em virtude do esgotamento do solvente (regime $\eta = 0,5$) ou da dissolução exaustiva das frações finas e médias.

Para capturar essa dinâmica multiescalar sem impor oscilações artificiais ou instabilidades numéricas, a trajetória de retração linear $|v(t)|$ de cada ensaio individual foi modelada por uma função contínua bi-exponencial estritamente não-negativa, parametrizada pelo vetor $\boldsymbol{\theta} = [a_1, b_1, a_2, b_2, c]^T$, formalizada pela Equação (4.31):

$$|v(t; \boldsymbol{\theta})| = a_1 \cdot \exp(-b_1 \cdot t) + a_2 \cdot \exp(-b_2 \cdot t) + c \tag{4.31}$$

com a velocidade com sinal físico de dissolução dada por $v(t; \boldsymbol{\theta}) = - |v(t; \boldsymbol{\theta})| \le 0$, sendo:
- $a_1 \ge 0$: amplitude da componente cinética ultrarrápida inicial ($\mu\text{m}\cdot\text{min}^{-1}$);
- $b_1 > 0$: constante de decaimento temporal de primeira ordem do pulso inicial ($\text{min}^{-1}$);
- $a_2 \ge 0$: amplitude da componente cinética intermediária ($\mu\text{m}\cdot\text{min}^{-1}$);
- $b_2 > 0$: constante de decaimento temporal do regime intermediário ($\text{min}^{-1}$);
- $c \ge 0$: velocidade residual assintótica em tempos longos ($\mu\text{m}\cdot\text{min}^{-1}$).

---

### 4.7.3. Solução Analítica Exata do Deslocamento Cumulativo $\delta(t)$

Conforme demonstrado pelo Método das Características na Subseção 4.5 (Equação 4.23), a conversão mássica $X_{\text{Zn}}$ depende unicamente do operador de encolhimento diametral acumulado $\delta(t) = \int_0^t |v(\tau)|\, d\tau$. A grande vantagem analítica da formulação bi-exponencial proposta na Equação (4.31) reside no fato de sua integral temporal possuir **solução fechada exata**, expressa pela Equação (4.32):

$$\delta(t; \boldsymbol{\theta}) = \frac{a_1}{b_1} \left[ 1 - \exp(-b_1 \cdot t) \right] + \frac{a_2}{b_2} \left[ 1 - \exp(-b_2 \cdot t) \right] + c \cdot t \tag{4.32}$$

com $\delta(0; \boldsymbol{\theta}) = 0$. Como $a_1, a_2, b_1, b_2, c \ge 0$, a Equação (4.32) garante formalmente que:
- $\delta(t)$ é uma função estritamente analítica, contínua e diferenciável $\forall t \ge 0$;
- $d\delta/dt = |v(t)| \ge 0$, assegurando monotonicidade estrita sem risco de flutuações numéricas;
- O cálculo de $\delta(t)$ é executado em tempo de máquina quase instantâneo, dispensando métodos iterativos de integração numérica de ODE durante a convergência do algoritmo de otimização.

O perfil de conversão predito associado a um determinado conjunto de parâmetros $\boldsymbol{\theta}$ é então obtido diretamente pela convolução populacional pré-computada do resolvedor mecanicista (Equações 4.25 a 4.27):

$$X_{\text{pred}}(t; \boldsymbol{\theta}) = \mathcal{F}_{\text{PBM}}\left( \delta(t; \boldsymbol{\theta}) \right) = 1 - \frac{M_3(\delta(t; \boldsymbol{\theta}))}{M_{3,0}} \tag{4.33}$$

---

### 4.7.4. Formulação da Função Objetivo e Otimização Numérica com Multi-Start

A estimação dos parâmetros ótimos $\boldsymbol{\theta}^*$ para cada um dos 16 ensaios de bancada foi formulada como um problema de mínimos quadrados não-lineares com restrições de caixa (*box constraints*) e termos de regularização física suave na cauda temporal assintótica:

$$\min_{\boldsymbol{\theta}} \mathcal{J}(\boldsymbol{\theta}) = \sum_{i=1}^{N_{\text{exp}}} \left[ X_{\text{pred}}(t_i; \boldsymbol{\theta}) - X_{\text{exp}}(t_i) \right]^2 + \lambda_{\text{tail}} \cdot \left[ |v(15; \boldsymbol{\theta})| \right]^2 + \lambda_{\delta} \cdot \left[ \max\left( 0,\ \delta(15; \boldsymbol{\theta}) - D_{\max} \right) \right]^2 \tag{4.34}$$

sendo $N_{\text{exp}} = 8$ o número de pontos temporais medidos no ensaio, $\lambda_{\text{tail}} = 10^{-4}$ o fator de regularização que penaliza velocidades residuais não-nulas no encerramento da batelada ($t = 15\ \text{min}$) e $\lambda_{\delta} = 10^{-5}$ o termo de barreira que impede deslocamentos diametrais superiores ao diâmetro máximo da população de partículas ($D_{\max} = 300\ \mu\text{m}$).

Para garantir o significado físico-químico dos coeficientes e evitar regiões não-físicas do espaço de parâmetros, estabeleceram-se limites rígidos de busca informados pela fenomenologia:
- $a_1 \in [0,0;\ 1200,0]\ \mu\text{m}\cdot\text{min}^{-1}$ (capacidade de absorver o pico ultrarrápido inicial);
- $b_1 \in [0,1;\ 50,0]\ \text{min}^{-1}$ (amortecimento acentuado nos primeiros segundos de reação);
- $a_2 \in [0,0;\ 500,0]\ \mu\text{m}\cdot\text{min}^{-1}$ (cinética intermediária de ataque difusivo/superficial);
- $b_2 \in [0,05;\ 20,0]\ \text{min}^{-1}$ (decaimento moderado da reação secundária);
- $c \in [0,0;\ 0,1]\ \mu\text{m}\cdot\text{min}^{-1}$ (velocidade assintótica estritamente contida próxima de zero).

A minimização da Equação (4.34) foi conduzida via algoritmo quase-Newton L-BFGS-B (*Limited-memory Broyden-Fletcher-Goldfarb-Shanno with Boundary constraints*), implementado na rotina `scipy.optimize.minimize` com tolerância de convergência estrita de $10^{-8}$. Para contornar a possibilidade de aprisionamento em mínimos locais decorrentes da não-linearidade da função $X_{\text{pred}}(\delta)$, utilizou-se uma estratégia de múltiplos pontos de partida (*multi-start*) composta por quatro estimativas iniciais distintas cobrindo diferentes ordens de grandeza cinéticas.

---

### 4.7.5. Validação da Reconstrução e Estruturação das Bases de Dados

A otimização inversa convergiu com absoluto sucesso para todos os 16 ensaios de bancada da matriz fatorial, alcançando um coeficiente de determinação global extraordinário:

$$R^2_{\text{global}} = 0{,}99896 \quad (\text{com } R^2 > 0{,}990 \text{ em todos os 16 ensaios individualmente})$$

com Raiz do Erro Quadrático Médio global $\text{RMSE} = 0{,}0098$ e Erro Médio Absoluto $\text{MAE} = 0{,}0071$, comprovando que a parametrização bi-exponencial acoplada ao Balanço Populacional é capaz de reconstituir integralmente a trajetória real de lixiviação de zinco sem perdas de informação física.

A partir dos parâmetros ótimos $\boldsymbol{\theta}^*$ obtidos para cada ensaio, foram consolidadas e exportadas três bases de dados fundamentais em formato CSV (armazenadas em `Base de dados/processed/`):
1. **Base de Alvos Discretos (`alvos_v_treinamento.csv`)**: contendo 128 registros pareados nos instantes exatos de medição experimental ($16\ \text{ensaios} \times 8\ \text{tempos}$), com os valores verdadeiros de $|v(t)|$, $\delta(t)$, $X_{\text{Zn,pred}}$ e $X_{\text{Zn,exp}}$;
2. **Base de Alvos em Malha Fina Regular (`alvos_v_treinamento_denso.csv`)**: contendo 976 registros gerados em uma grade temporal uniforme com passo fino de $\Delta t = 0{,}25\ \text{min}$ ($61\ \text{nós por ensaio}$ no intervalo de $0$ a $15\ \text{min}$), essencial para mitigar o sobre-ajuste (*overfitting*) e propiciar suporte contínuo de interpolação aos algoritmos de regressão e redes neurais;
3. **Tabela de Parâmetros Ótimos (`parametros_otimizacao_inversa.csv`)**: registrando os cinco coeficientes ajustados $(a_1, b_1, a_2, b_2, c)$, as velocidades iniciais $|v_0|$, o encolhimento total final $\delta_{15}$ e os indicadores estatísticos ($R^2$, RMSE, MAE) de cada condição experimental.

Essas bases de dados constituem os dados rotulados (*labeled targets*) definitivos para o treinamento supervisionado dos modelos orientados por dados nas etapas seguintes.
