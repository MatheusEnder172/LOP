## 4.8. Pré-Processamento, Engenharia de Atributos e Estratégia de Partição de Dados

Nesta subseção são detalhados a formulação do espaço vetorial de atributos de entrada, a fundamentação físico-química da partição espacial 85/15 dos dados cinéticos, a blindagem metodológica contra vazamento de informação (*data leakage*) via validação cruzada agrupada por ensaio (`GroupKFold`), o protocolo de escalonamento estatístico e a transformação logarítmica empregada para assegurar a não-negatividade termodinâmica da taxa de retração interfacial.

---

### 4.8.1. Definição do Espaço de Atributos e Variável Alvo

Para que os modelos orientados por dados (*Data-Driven Models* — DDM) aprendam a inferir com fidelidade a taxa linear de retração de diâmetro de partícula $|v(t)|$, é imperativo alimentá-los com as variáveis de estado e condições operacionais que influenciam diretamente a cinética de dissolução heterogênea.

O vetor de características de processo para cada observação no tempo, denotado por $\mathbf{x} \in \mathbb{R}^4$, foi estruturado pelas seguintes grandezas termodinâmicas e temporais:

$$\mathbf{x} = \left[ T,\ C_{A0},\ \eta,\ t \right]^T \tag{4.35}$$

sendo:
- $T$: temperatura absoluta de lixiviação ($T = 40{,}0\ ^\circ\text{C}$ constante nos ensaios de bancada de Bortot Coelho (2017), incluída formalmente como dimensão ativa no vetor de entrada para permitir futura generalização térmica Arrhenius);
- $C_{A0}$: concentração molar inicial de ácido sulfúrico livre no licor de ataque ($0{,}10 \le C_{A0} \le 1{,}50\ \text{mol}\cdot\text{L}^{-1}$);
- $\eta$: razão molar estequiométrica entre o ácido alimentado e a zincita presente no minério ($\eta = n_{\text{H}_2\text{SO}_4,0} / n_{\text{ZnO},0}$, variando de $0{,}5$ a $3{,}1$);
- $t$: tempo transcorrido de reação em batelada ($0{,}0 \le t \le 15{,}0\ \text{min}$).

A variável escalar de saída (alvo supervisionado), denotada por $y \in \mathbb{R}^+$, é o módulo da taxa de retração interfacial instantânea deduzida pela otimização inversa na Subseção 4.7:

$$y = |v(t)| = \left| \frac{dD}{dt} \right| \ge 0 \quad (\mu\text{m}\cdot\text{min}^{-1}) \tag{4.36}$$

---

### 4.8.2. Estratégia de Partição Espacial 85/15 e Critérios Físico-Químicos

Diferentemente de problemas clássicos de aprendizado de máquina tabular em que as amostras são sorteadas de forma puramente aleatória, dados provenientes de séries temporais de engenharia de processos particionados ao acaso sofrem invariavelmente de severo **vazamento de dados** (*data leakage*). Se observações de um mesmo ensaio fossem distribuídas simultaneamente entre treino e teste, o modelo estaria meramente interpolando pontos temporais vizinhos de uma curva já conhecida, gerando uma falsa impressão de acurácia que se degradaria catastroficamente na predição de um novo experimento completo.

Para assegurar uma avaliação imparcial e representativa da capacidade de generalização espacial dos algoritmos, a base de dados cinéticos de bancada foi particionada sob o paradigma **85/15 baseado em ensaios completos disjuntos**:
- **Conjunto de Treino e Calibração (81,25% dos ensaios)**: composto por 13 ensaios experimentais (totalizando 793 amostras na grade densa e 104 medições pontuais);
- **Conjunto de Teste Cego Independente (18,75% dos ensaios)**: composto por 3 ensaios inteiros rigorosamente mantidos intocados durante todas as fases de calibração, sintonia e seleção de hiperparâmetros (totalizando 183 amostras na grade densa e 24 medições pontuais).

A escolha dos três ensaios que compõem o conjunto de teste cego (**Ensaios 8, 14 e 7**) atendeu a quatro restrições estritas de consistência hidrometalúrgica e geométrica:

1. **Preservação Integral do Envoltório Convexo (*Convex Hull*)**:
   Todos os quatro cantos extremos da matriz fatorial experimental — isto é, as combinações limítrofes $(C_{A0} = 0{,}10\ \text{mol/L},\ \eta = 0{,}5)$, $(C_{A0} = 0{,}10\ \text{mol/L},\ \eta = 3{,}1)$, $(C_{A0} = 1{,}50\ \text{mol/L},\ \eta = 0{,}5)$ e $(C_{A0} = 1{,}50\ \text{mol/L},\ \eta = 3{,}1)$ —, bem como as bordas externas da matriz, permaneceram 100% no conjunto de calibração. Isso garante que a avaliação em teste cego meça rigorosamente a **capacidade de interpolação não-linear** do modelo dentro do domínio de treino, evitando que falhas de extrapolação geométrica precoce mascarem o potencial intrínseco dos algoritmos;
2. **Alternância entre Níveis Intermediários de Ácido**:
   Os ensaios de teste cobrem concentrações de reagente situadas no miolo da matriz operacional:
   - Ensaio 8: $C_{A0} = 0{,}50\ \text{mol/L}$ e $\eta = 1{,}0$ (lixiviação neutra estequiométrica);
   - Ensaio 14: $C_{A0} = 1{,}00\ \text{mol/L}$ e $\eta = 1{,}5$ (leve excesso de solvente);
   - Ensaio 7: $C_{A0} = 0{,}50\ \text{mol/L}$ e $\eta = 3{,}1$ (forte excesso de solvente);
3. **Representatividade Fenomenológica dos Regimes de Dissolução**:
   O conjunto de teste cego abrange os três comportamentos assintóticos observados na lixiviação:
   - O Ensaio 8 representa o regime neutro com desaceleração profunda e conversão assintótica contida em $87\%$;
   - O Ensaio 14 representa o regime de superávit brando com conversão elevada atingindo $97\%$;
   - O Ensaio 7 representa o regime superácido ultrarrápido com conversão plena de $100\%$;
4. **Proteção Rigorosa do Regime Limitante de Solvente ($\eta = 0{,}5$)**:
   Todos os 4 ensaios caracterizados por deficiência estequiométrica de ácido (Ensaios 1, 2, 9 e 10) foram mantidos integralmente no conjunto de calibração. Essa blindagem foi mandatória para garantir que os algoritmos de aprendizado de máquinas aprendessem a impor a redução drástica de velocidade decorrente do esgotamento precoce de ácido ($X_{\text{Zn}} \approx 0{,}50$).

A Tabela 4.7 detalha a distribuição das condições experimentais entre os conjuntos de calibração e teste cego.

Tabela 4.7 – Matriz de partição dos ensaios de bancada (Estratégia 85/15 disjunta).

| Ensaio | $C_{A0}$ (mol/L) | Razão $\eta$ (-) | Partição Metodológica | Justificativa Físico-Química |
| :---: | :---: | :---: | :---: | :--- |
| **1** | 0,10 | 0,5 | Treino / Calibração | Vértice inferior do *Convex Hull* (esgotamento ácido) |
| **2** | 0,20 | 0,5 | Treino / Calibração | Regime de esgotamento ácido |
| **3** | 0,10 | 1,0 | Treino / Calibração | Vértice de baixa acidez em regime neutro |
| **4** | 0,20 | 1,0 | Treino / Calibração | Regime neutro de baixa acidez |
| **5** | 0,10 | 1,5 | Treino / Calibração | Regime de excesso moderado em baixa acidez |
| **6** | 0,20 | 1,5 | Treino / Calibração | Regime de excesso moderado em baixa acidez |
| **7** | **0,50** | **3,1** | **Teste Cego (18,75%)** | **Regime de forte excesso e acidez intermediária** |
| **8** | **0,50** | **1,0** | **Teste Cego (18,75%)** | **Regime estequiométrico neutro com atenuação assintótica** |
| **9** | 0,50 | 0,5 | Treino / Calibração | Regime de esgotamento ácido em acidez intermediária |
| **10** | 1,50 | 0,5 | Treino / Calibração | Vértice de esgotamento ácido em alta acidez |
| **11** | 1,50 | 1,0 | Treino / Calibração | Borda externa de alta acidez em regime neutro |
| **12** | 0,10 | 3,1 | Treino / Calibração | Vértice extremo de alta razão em baixa acidez |
| **13** | 0,20 | 3,1 | Treino / Calibração | Regime de alta razão em baixa acidez |
| **14** | **1,00** | **1,5** | **Teste Cego (18,75%)** | **Regime de leve excesso ácido e alta concentração** |
| **15** | 1,50 | 1,5 | Treino / Calibração | Borda externa de alta acidez e leve excesso |
| **16** | 1,50 | 3,1 | Treino / Calibração | Vértice superior do *Convex Hull* (alta acidez e forte excesso) |

Fonte: Elaborada pelos autores a partir do planejamento fatorial de Bortot Coelho (2017).

---

### 4.8.3. Protocolo de Validação Cruzada Espacial (`GroupKFold`)

Para a seleção de hiperparâmetros, avaliação de viés-variância e prevenção de sobre-ajuste (*overfitting*) durante o treinamento dos modelos no conjunto de calibração, implementou-se o algoritmo de **Validação Cruzada Agrupada em 4 Dobras** (`GroupKFold`, $K = 4$).

Nessa abordagem, a variável indicadora do ensaio (`ensaio_id`) foi definida como a chave de agrupamento (*group identifier*). Dessa forma, a partição garante rigorosamente que:
- Todos os 61 pontos temporais densos de um mesmo ensaio pertençam integralmente à dobra de treino ou integralmente à dobra de validação;
- A métrica de validação cruzada avalia a capacidade do modelo em extrapolar a cinética para **ensaios inteiros não observados na respectiva dobra**, simulando realisticamente o comportamento frente ao conjunto de teste cego final.

A Tabela 4.8 apresenta a distribuição dos 13 ensaios de calibração entre as 4 dobras disjuntas do `GroupKFold`.

Tabela 4.8 – Configuração das dobras de validação cruzada espacial (`GroupKFold`, 4 dobras).

| Dobra (*Fold*) | Ensaios de Validação ($N_{\text{val}} = 3\text{ ou }4$) | Amostras Densas Validação | Ensaios de Calibração ($N_{\text{treino}} = 9\text{ ou }10$) | Amostras Densas Calibração |
| :---: | :--- | :---: | :--- | :---: |
| **Dobra 1** | Ensaios 1, 5 e 11 | 183 | Ensaios 2, 3, 4, 6, 9, 10, 12, 13, 15 e 16 | 610 |
| **Dobra 2** | Ensaios 2, 6 e 12 | 183 | Ensaios 1, 3, 4, 5, 9, 10, 11, 13, 15 e 16 | 610 |
| **Dobra 3** | Ensaios 3, 9 e 15 | 183 | Ensaios 1, 2, 4, 5, 6, 10, 11, 12, 13 e 16 | 610 |
| **Dobra 4** | Ensaios 4, 10, 13 e 16 | 244 | Ensaios 1, 2, 3, 5, 6, 9, 11, 12 e 15 | 549 |

Fonte: Elaborada pelos autores (2026).

---

### 4.8.4. Escalonamento Estatístico e Transformação Logarítmica do Alvo

Em virtude das disparidades de magnitude e unidade entre as variáveis do vetor de entrada $\mathbf{x}$ — onde $T = 40$, $C_{A0} \in [0,10; 1,50]$, $\eta \in [0,5; 3,1]$ e $t \in [0; 15]$ —, algoritmos baseados em descida de gradiente (como redes neurais MLP) e métodos de margem por distâncias euclidianas (como SVR) degradariam severamente sua convergência caso operassem sobre grandezas brutas (Bishop, 2006).

Para homogeneizar a sensibilidade numérica, foi aplicado o escalonamento padronizado $Z$-score (`StandardScaler`) a cada dimensão $j$ do vetor de características:

$$x_{j,\text{norm}} = \frac{x_j - \mu_j}{\sigma_j} \tag{4.37}$$

sendo $\mu_j$ e $\sigma_j$ a média amostral e o desvio padrão da $j$-ésima variável. Sob o rigor metodológico de proteção contra vazamento estatístico, a classe `FeatureTargetScaler` computou $\mu_j$ e $\sigma_j$ **exclusivamente a partir das 793 amostras do conjunto de calibração** (`fit`), sendo os mesmos transformadores estáticos reaplicados às dobras de validação e ao conjunto de teste cego (`transform`).

Para a variável alvo $|v(t)|$, a natureza do processo heterogêneo impõe duas características matemáticas singulares:
1. Uma assimetria positiva extrema (*skewness* acentuada), com valores decaindo de $\approx 600\ \mu\text{m/min}$ nos primeiros instantes para menos de $5\ \mu\text{m/min}$ em tempos longos;
2. A restrição física inegociável de **não-negatividade**: $|v(t)| \ge 0$, uma vez que uma taxa linear em módulo negativa violaria o princípio de conservação de massa e implicaria o crescimento espontâneo do raio da partícula durante a lixiviação.

Para acomodar ambas as restrições simultaneamente, o alvo supervisionado foi submetido à transformação logarítmica invertível $\text{log1p}$:

$$z = \ln\left( 1 + |v| \right) \tag{4.38}$$

com o mapeamento inverso exato garantido por:

$$|v_{\text{pred}}| = \max\left( 0,\ \exp(z_{\text{pred}}) - 1 \right) \tag{4.39}$$

A formulação dada pela Equação (4.39) garante matematicamente que, mesmo que o regressor infira pontualmente um valor $z_{\text{pred}} < 0$ em regiões de cauda assintótica, a velocidade de retração interfacial permanecerá **estritamente não-negativa por construção analítica**, eliminando anomalias físicas na subsequente integração do Balanço Populacional.
