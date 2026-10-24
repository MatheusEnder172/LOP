## 4.3. Metodologia de Caracterização e Modelagem da Distribuição Granulométrica (RRB)

Nesta subseção são detalhados os métodos de medição experimental do espectro granulométrico da matéria-prima, a formulação matemática do modelo analítico de Rosin-Rammler-Bennet (RRB), o procedimento de linearização e estimação de parâmetros, a discretização numérica do domínio contínuo de diâmetros de partículas e a conexão formal com a teoria de momentos do Balanço Populacional. O foco desta etapa é estritamente metodológico, detalhando como os dados granulométricos foram tratados e como a condição inicial contínua do reator heterogêneo foi estruturada computacionalmente. A discussão aprofundada dos parâmetros obtidos e suas implicações cinéticas é apresentada na Seção 5 (Resultados e Discussão).

---

### 4.3.1. Relevância Metodológica da Distribuição Granulométrica no Balanço Populacional

Em sistemas reacionais heterogêneos sólido-líquido em que a fase sólida é constituída por um material particulado polidisperso, a taxa global de reação é fortemente condicionada pela área superficial total disponível para contato com o reagente lixiviante. A adoção de um diâmetro médio representativo único (abordagem de partícula média) introduz distorções severas: subestima a reatividade nos instantes iniciais — governada pela dissolução quase instantânea dos grãos finos de elevadíssima área específica — e superestima a velocidade nas etapas finais, cujo tempo de esgotamento é controlado pelas partículas de maior calibre (LeBlanc; Fogler, 1987; Randolph; Larson, 1988).

Para superar essa limitação, a modelagem fenomenológica baseada no Balanço Populacional (PBM) trata o tamanho da partícula como uma coordenada interna contínua ($D$), governada pela Equação Diferencial Parcial hiperbólica de conservação populacional (Randolph; Larson, 1988), expressa para um reator batelada sem quebra nem aglomeração por:

$$\frac{\partial \psi(D, t)}{\partial t} = - \frac{\partial [ v(D, t) \cdot \psi(D, t) ]}{\partial D}$$

sendo $\psi(D, t)$ a função densidade de distribuição populacional no instante $t$ e $v(D, t) = dD/dt$ a velocidade linear de dissolução interfacial. Para a integração numérica dessa formulação mecanicista, é metodologicamente indispensável conhecer a condição inicial da população no instante de alimentação do reator ($t = 0$):

$$\psi(D, 0) = N_T(0) \cdot f_0(D)$$

em que $N_T(0)$ é o número total de partículas por unidade de volume e $f_0(D)$ é a função densidade de probabilidade inicial de tamanho de partículas. Como as determinações experimentais fornecem medições discretas em peneiras e canais ópticos finitos, torna-se obrigatório ajustar uma função contínua, analítica e diferenciável que represente fidedignamente todo o espectro granulométrico do concentrado.

---

### 4.3.2. Procedimentos Experimentais de Determinação Granulométrica

Os dados experimentais de distribuição de tamanho de partículas da calcina de zinco foram obtidos a partir das medições reportadas na dissertação de mestrado de Bortot Coelho (2017, Capítulo 5, Tabela 5.4, p. 129). Em virtude da ampla faixa granulométrica da matéria-prima industrial — que se estende por quase três ordens de grandeza, desde frações submicrométricas ($0,45\ \mu\text{m}$) até partículas da ordem de $300\ \mu\text{m}$ —, adotou-se uma metodologia combinada integrando duas técnicas analíticas complementares:

1. **Peneiramento a úmido**: Aplicado para a quantificação das frações grosseiras e intermediárias, utilizando uma série de 8 peneiras de malha quadrada padrão Tyler com aberturas de malha compreendidas entre $38\ \mu\text{m}$ e $297\ \mu\text{m}$ (malhas Tyler 400#, 325#, 270#, 200#, 150#, 100#, 65# e 48#). O procedimento a úmido foi rigorosamente selecionado em substituição ao peneiramento a seco para evitar a aglomeração eletrostática de partículas finas sobre as malhas e minimizar perdas por poeira;
2. **Difração de raios laser**: Empregada para a caracterização precisa da fração ultrafina passante na malha Tyler 200# ($74\ \mu\text{m}$), na faixa de medição entre $0,45\ \mu\text{m}$ e $74,0\ \mu\text{m}$. A análise foi conduzida em analisador de tamanho de partículas por difração a laser Helos 12LA da Sympatec GmbH, utilizando módulo de dispersão via líquida com pré-tratamento por banho ultrassônico de alta frequência para a desaglomeração completa dos pós antes da leitura óptica.

No ponto de sobreposição instrumental das duas técnicas (abertura de $74\ \mu\text{m}$, correspondente à malha 200# Tyler), ambas registraram exatamente 84,4% de fração mássica acumulada passante, confirmando a concordância metodológica e a continuidade física dos dados empíricos entre as duas faixas instrumentais (Bortot Coelho, 2017).

---

### 4.3.3. Formulação Matemática do Modelo de Rosin-Rammler-Bennet (RRB)

Para descrever analiticamente a distribuição de tamanhos do concentrado de zinco obtida por moagem e ustulação industrial, selecionou-se a distribuição empírico-analítica de Rosin-Rammler-Bennet (Rosin; Rammler, 1933; Bennet, 1936), consagrada na literatura de tratamento de minérios e engenharia química para materiais particulados polidispersos finos.

A função de distribuição mássica acumulada passante $F(D)$, correspondente à fração em massa de sólidos composta por partículas de diâmetro menor ou igual a $D$, é formalizada pela Equação (4.7):

$$F(D) = 1 - \exp\left[ - \left( \frac{D}{D'_{63,2}} \right)^m \right] \tag{4.7}$$

sendo:
- $D$: diâmetro característico da partícula ($\mu\text{m}$);
- $D'_{63,2}$: diâmetro característico de escala da amostra ($\mu\text{m}$), definido analiticamente como a abertura para a qual a fração acumulada passante é igual a $F(D'_{63,2}) = 1 - e^{-1} \approx 0,6321$ (ou 63,21% em massa);
- $m$: módulo de uniformidade ou dispersão da distribuição (adimensional). Valores de $m$ próximos da unidade ($m \approx 1,0$) indicam uma ampla dispersão de tamanhos com presença acentuada de frações ultrafinas, enquanto valores elevados ($m > 3$) caracterizam distribuições estreitas e quase monodispersas.

---

### 4.3.4. Metodologia de Linearização e Estimação de Parâmetros

A determinação dos parâmetros constitutivos do modelo ($D'_{63,2}$ e $m$) a partir dos pares experimentais $(D_i, F_{\text{exp},i})$ foi implementada por meio da transformação dupla logarítmica de Weibull (Bennet, 1936; Montgomery; Runger, 2010), obtida isolando-se o termo exponencial da Equação (4.7) e aplicando-se a função logarítmica por duas vezes sucessivas, conforme deduzido na Equação (4.8):

$$\ln\left[ \ln\left( \frac{1}{1 - F(D)} \right) \right] = m \cdot \ln(D) - m \cdot \ln(D'_{63,2}) \tag{4.8}$$

Definindo as variáveis linearizadas:
- $Y = \ln\left[ \ln\left( \frac{1}{1 - F(D)} \right) \right]$
- $X = \ln(D)$
- $a = m$ (coeficiente angular da reta)
- $b = - m \cdot \ln(D'_{63,2})$ (coeficiente linear da reta)

a Equação (4.8) assume a forma clássica de regressão linear $Y = aX + b$. O protocolo computacional desenvolvido em Python executou os seguintes passos metodológicos:

1. **Transformação dos dados**: Aplicação das transformações não-lineares aos pares $(D_i, F_{\text{exp},i})$ provenientes de Bortot Coelho (2017, Tabela 5.4), excluindo-se eventuais pontos singulares em $F = 0$ ou $F = 1$;
2. **Regressão linear ordinária**: Ajuste por Mínimos Quadrados Ordinários (OLS) para obter as estimativas preliminares dos parâmetros $a$ e $b$, a partir dos quais computa-se $m = a$ e $D'_{63,2} = \exp(-b/a)$;
3. **Refinamento não-linear**: Utilização das estimativas obtidas na regressão linearizada como valores iniciais para algoritmo de otimização não-linear de Levenberg-Marquardt (rotina `scipy.optimize.curve_fit`), minimizando diretamente a soma dos resíduos quadráticos na escala original da fração acumulada $F(D)$ (Equação 4.7).

Os parâmetros de ajuste resultantes desse procedimento reproduziram os valores estabelecidos na dissertação de referência: $D'_{63,2} = 41,65\ \mu\text{m}$ e $m = 1,022$ (Bortot Coelho, 2017, Tabela 5.6 e Tabela 5.9).

---

### 4.3.5. Derivação das Funções Densidade e Teoria dos Momentos Volumétricos

Para a resolução do Balanço Populacional, é necessário derivar a função densidade de probabilidade volumétrica e relacioná-la aos momentos estatísticos da população de sólidos. A função densidade de distribuição contínua volumétrica/mássica $f_3(D)$ é obtida pela diferenciação analítica de $F(D)$ em relação ao diâmetro $D$, expressa pela Equação (4.9):

$$f_3(D) = \frac{dF(D)}{dD} = \frac{m}{D'_{63,2}} \cdot \left( \frac{D}{D'_{63,2}} \right)^{m-1} \cdot \exp\left[ - \left( \frac{D}{D'_{63,2}} \right)^m \right] \tag{4.9}$$

sendo que a propriedade de normalização de probabilidade é estritamente satisfeita no domínio contínuo:

$$\int_0^\infty f_3(D)\, dD = 1$$

Na teoria formal de processos particulados (Randolph; Larson, 1988), o $j$-ésimo momento da função densidade numérica populacional $n(D, t)$ é definido pela Equação (4.10):

$$M_j(t) = \int_0^\infty D^j \cdot n(D, t)\, dD \tag{4.10}$$

Cada momento possui um significado físico-geométrico direto no sistema de lixiviação:
- $M_0(t)$: número total de partículas por unidade de volume de polpa;
- $M_1(t)$: comprimento acumulado das partículas;
- $M_2(t)$: proporcional à área superficial total interfacial das partículas sólidas ($A_p(t) = k_a \cdot M_2(t)$, sendo $k_a = \pi$ para esferas);
- $M_3(t)$: proporcional ao volume total ocupado pela fase sólida ($V_s(t) = k_v \cdot M_3(t)$, sendo $k_v = \pi/6$ o fator de forma volumétrico para partículas esféricas).

O terceiro momento volumétrico no instante inicial ($t = 0$) é avaliado integrando-se a função densidade sobre todo o domínio geométrico de partículas alimentadas, conforme a Equação (4.11):

$$M_3(0) = \int_{D_{\min}}^{D_{\max}} D^3 \cdot n(D, 0)\, dD = \frac{V_s(0)}{k_v} \tag{4.11}$$

A conversão fracionária de zincita $X_{\text{Zn}}(t)$ em qualquer tempo reacional subsequente pode então ser avaliada a partir do consumo relativo de volume sólido previsto pelo Balanço Populacional, formalizada pela Equação (4.12):

$$X_{\text{Zn}}(t) = 1 - \frac{M_3(t)}{M_3(0)} \tag{4.12}$$

A Equação (4.12) demonstra metodologicamente que o cálculo rigoroso do terceiro momento inicial $M_3(0)$ é o alicerce numérico que acopla o avanço da dissolução física das partículas com a fração convertida monitorada experimentalmente.

Adicionalmente, a partir das propriedades analíticas da função Gama de Euler $\Gamma(\cdot)$, deduz-se o diâmetro médio característico da distribuição de Rosin-Rammler-Bennet ($\bar{D}$), expresso pela Equação (4.13):

$$\bar{D} = D'_{63,2} \cdot \Gamma\left( 1 + \frac{1}{m} \right) \tag{4.13}$$

Para os parâmetros nominais ($D'_{63,2} = 41,65\ \mu\text{m}$ e $m = 1,022$), a avaliação da Equação (4.13) fornece o diâmetro médio analítico da calcina em $\bar{D} = 41,28\ \mu\text{m}$, reproduzindo com exatidão o valor reportado por Bortot Coelho (2017, p. 133).

---

### 4.3.6. Discretização Numérica do Domínio Granulométrico e Validação do Módulo

Para permitir a integração numérica computacional das equações diferenciais do Balanço Populacional, o domínio contínuo de diâmetros foi discretizado em uma malha geométrica refinada em ambiente Python, encapsulada no módulo de primeiros princípios de granulometria.

O protocolo numérico adotado seguiu as seguintes diretrizes de discretização:

1. **Delimitação do domínio físico**: Fixou-se o intervalo de integração entre o diâmetro mínimo $D_{\min} = 0,01\ \mu\text{m}$ (limite inferior assintótico abaixo do qual a massa residual é desprezível, $F(D_{\min}) < 10^{-4}$) e o diâmetro máximo $D_{\max} = 297,0\ \mu\text{m}$ (abertura da peneira 48# Tyler correspondente a 100% de passante experimental);
2. **Discretização logarítmica de malha**: A malha unidimensional de diâmetros foi gerada com espaçamento logarítmico (ou potência geométrica) contendo $N = 1000$ nós, concentrando intencionalmente maior densidade de pontos na região de partículas finas ($D < 20\ \mu\text{m}$). A justificativa metodológica dessa escolha reside no fato de que o gradiente de encolhimento e a taxa de desaparecimento de partículas finas são extremamente intensos nos primeiros instantes de reação, demandando resolução espacial refinada para evitar difusão numérica artificial;
3. **Integração numérica do terceiro momento**: A integração do terceiro momento inicial $M_3(0)$ (Equação 4.11) na malha discretizada foi conduzida pela regra trapezoidal composta vetorizada. A validação numérica do algoritmo foi executada comparando o resultado trapezoidal com a integração por quadratura adaptativa de Gauss-Kronrod de alta ordem (`scipy.integrate.quad`), registrando discrepância relativa inferior a $0,00001\%$, garantindo convergência com precisão de máquina.

A conformidade do ajuste da distribuição analítica RRB frente aos dados experimentais empíricos foi verificada pelas seguintes métricas estatísticas:

$$R^2 = 1 - \frac{\sum_{i=1}^N (F_{\text{exp},i} - F_{\text{calc},i})^2}{\sum_{i=1}^N (F_{\text{exp},i} - \bar{F}_{\text{exp}})^2}$$

$$\text{RMSE} = \sqrt{ \frac{1}{N} \sum_{i=1}^N (F_{\text{exp},i} - F_{\text{calc},i})^2 }$$

$$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |F_{\text{exp},i} - F_{\text{calc},i}|$$

A Tabela 4.2 sintetiza as propriedades físicas, os parâmetros constitutivos e as métricas de validação computacional do modelo granulométrico RRB.

**Tabela 4.2 – Parâmetros constitutivos e métricas estatísticas de validação do modelo granulométrico de Rosin-Rammler-Bennet para a calcina de zinco.**

| Propriedade / Parâmetro | Símbolo | Valor | Unidade | Método / Fonte |
| :--- | :---: | :---: | :---: | :--- |
| Diâmetro característico de escala | $D'_{63,2}$ | 41,65 | $\mu\text{m}$ | Regressão não-linear / Bortot Coelho (2017) |
| Módulo de uniformidade / dispersão | $m$ | 1,022 | - | Regressão linearizada de Weibull (Eq. 4.8) |
| Diâmetro médio analítico | $\bar{D}$ | 41,28 | $\mu\text{m}$ | Função Gama de Euler (Eq. 4.13) |
| Densidade real das partículas sólidas | $\rho_s$ | 5,61 | $\text{g}\cdot\text{cm}^{-3}$ | Picnometria de líquidos a 25 °C |
| Densidade molar da zincita sólida | $\rho_{s,\text{mol}}$ | 69,2 | $\text{mol}\cdot\text{L}^{-1}$ | Balanço molar e pureza ($T_{\text{ZnO}} = 76,1\%$) |
| Fator de forma volumétrico | $k_v$ | $\pi/6 \approx 0,5236$ | - | Hipótese de esfericidade de partículas |
| Domínio de discretização de diâmetros | $[D_{\min}, D_{\max}]$ | $[0,01;\ 297,0]$ | $\mu\text{m}$ | Malha logarítmica com $N = 1000$ nós |
| Coeficiente de determinação global | $R^2$ | 0,9962 | - | Aderência do modelo RRB aos dados experimentais |
| Raiz do erro quadrático médio | $\text{RMSE}$ | 0,0210 | - | Desvio quadrático médio ($2,1\%$ em fração passante) |
| Erro absoluto médio | $\text{MAE}$ | 0,0142 | - | Resíduo linear médio ($1,4\%$ em fração passante) |
| $R^2$ da reta linearizada de Weibull | $R^2_{\text{lin}}$ | 0,9908 | - | Regressão linear $Y = 1,0223X - 3,8468$ |

*Fonte: Elaborado pelos autores a partir de dados de Bortot Coelho (2017, Capítulo 5, Tabelas 5.4, 5.6 e 5.9).*

---

### 4.3.7. Metodologia de Representação Gráfica Multiescalar

Para inspecionar visualmente a qualidade da representação em diferentes escalas de diâmetro e confirmar a acurácia do modelo RRB nas regiões limítrofes, desenvolveu-se uma rotina de visualização multiescalar em Python estruturada em um painel composto por quatro subplots dispostos em grade 2×2:

- **Painel (a) — Escala linear ($F$ vs. $D$)**: Avalia o comportamento global da curva acumulada passante e evidencia o diâmetro característico $D'_{63,2} = 41,65\ \mu\text{m}$ no ponto exato em que a fração passante intercepta 63,21% em massa;
- **Painel (b) — Escala semi-logarítmica ($F$ vs. $\log D$)**: Realça o perfil sigmoidal clássico da distribuição e permite inspecionar simultaneamente a concordância do modelo com os dados nas regiões extremas (cauda de partículas ultrafinas inferiores a $2\ \mu\text{m}$ e grãos grosseiros superiores a $150\ \mu\text{m}$);
- **Painel (c) — Função densidade de frequência $f_3(D)$**: Apresenta a curva diferencial de densidade volumétrica derivada analiticamente (Equação 4.9), assinalando a posição do diâmetro médio populacional ($\bar{D} = 41,28\ \mu\text{m}$);
- **Painel (d) — Linearização de Weibull/RRB**: Confronta os pontos empíricos transformados com a reta ajustada por Mínimos Quadrados Ordinários ($Y = 1,0223X - 3,8468$, $R^2 = 0,9908$), atestando a linearidade do modelo.

A Figura 4.2 ilustra o painel comparativo multiescalar resultante dessa rotina. A discussão interpretativa a respeito da distribuição granulométrica e seus desdobramentos sobre a cinética heterogênea do reator é detalhada na Seção 5 (Resultados e Discussão).

*(Inserir Figura 4.2 – Painel de análise granulométrica multiescalar do concentrado ustulado de zinco comparando dados experimentais combinados de peneiramento a úmido e difração a laser com o modelo de Rosin-Rammler-Bennet).*

*Fonte: Elaborado pelos autores a partir de dados de Bortot Coelho (2017, Capítulo 5, Tabela 5.4).*
