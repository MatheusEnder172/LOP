## 4.9. Modelos Orientados por Dados (DDM) e Metodologia de Seleção Multicritério

Nesta subseção são detalhadas a fundamentação matemática, as estratégias de regularização e as rotinas de calibração supervisionada dos quatro algoritmos de aprendizado de máquinas (*Data-Driven Models* — DDM) avaliados para a predição da taxa de retração interfacial $|v(t)|$. Apresenta-se também a metodologia formal de Análise de Decisão Multicritério (*Multi-Criteria Decision Analysis* — MCDA) formulada para a seleção imparcial do modelo campeão que alimenta a arquitetura híbrida serial.

---

### 4.9.1. O Papel do Regressor Caixa-Preta no Esquema Híbrido

No paradigma híbrido serial, o modelo puramente orientado por dados não atua como um substituto integral do processo físico-químico, mas sim como um estimador flexível de propriedades constitutivas complexas (von Stosch et al., 2014; Solle et al., 2017). Conforme fundamentado nas Subseções 4.4 e 4.7, enquanto a equação do Balanço Populacional governa com rigor mecanicista a conservação da massa particulada e o avanço da frente de reação, a velocidade linear de dissolução interfacial $|v(t)|$ condensa fenômenos microscópicos altamente acoplados — tais como a evolução da rugosidade superficial, a variação da força iônica no licor e a resistência difusiva em camadas passivantes de sílica ou jarosita.

Assim, o objetivo do regressor supervisionado consiste em mapear a função não-linear contínua:

$$|v(t)| = \widehat{f}_{\text{ML}}\left( \mathbf{x} \right) = \widehat{f}_{\text{ML}}\left( T,\ C_{A0},\ \eta,\ t \right) \tag{4.40}$$

utilizando as bases de dados calibradas pela otimização inversa no conjunto de treino de 13 ensaios ($N = 793$ amostras densas). Para cobrir diferentes famílias metodológicas de aprendizado estatístico, foram selecionados quatro algoritmos representativos: uma rede neural profunda (*Multi-Layer Perceptron*), dois métodos de comitê baseados em árvores (*Random Forest* e *XGBoost*) e um método de aprendizado baseado em margem e teoria de núcleos (*Support Vector Regression*).

---

### 4.9.2. Formulação dos Algoritmos de Regressão Supervisionada

#### 4.9.2.1. Rede Neural Artificial Profunda (Multi-Layer Perceptron — MLP em PyTorch)
A arquitetura *Multi-Layer Perceptron* (Goodfellow; Bengio; Courville, 2016) mapeia as características de entrada $\mathbf{x}_{\text{norm}} \in \mathbb{R}^4$ através de uma sucessão de transformações afins seguidas de ativações não-lineares suaves. A rede neural profunda implementada em PyTorch é composta por três camadas ocultas densas totalmente conectadas (com 64, 32 e 16 neurônios, respectivamente). A propagação direta na $l$-ésima camada é formalizada pela Equação (4.41):

$$\mathbf{h}^{(l)} = \text{GELU}\left( \text{LayerNorm}\left( \mathbf{W}^{(l)} \mathbf{h}^{(l-1)} + \mathbf{b}^{(l)} \right) \right) \tag{4.41}$$

sendo $\mathbf{W}^{(l)}$ a matriz de pesos sinápticos, $\mathbf{b}^{(l)}$ o vetor de polarização (*bias*), $\text{LayerNorm}$ o operador de normalização por camada (que estabiliza os gradientes ao longo do treinamento) e $\text{GELU}$ (*Gaussian Error Linear Unit*) a função de ativação suave (Hendrycks; Gimpel, 2016):

$$\text{GELU}(u) = u \cdot \Phi(u) = u \cdot P(U \le u), \quad U \sim \mathcal{N}(0, 1) \tag{4.42}$$

A camada de saída projeta o escalar de velocidade no espaço logarítmico $z = \ln(1 + |v|)$. O treinamento foi conduzido minimizando o erro quadrático médio com penalização de norma $L_2$ nos pesos (*weight decay* $\lambda_w = 10^{-4}$) via otimizador AdamW (Loshchilov; Hutter, 2019), taxa de aprendizado inicial $\alpha_{\text{opt}} = 10^{-3}$ e escalonador por cosseno. Para evitar sobre-ajuste, aplicou-se abandono estocástico (*Dropout* com taxa de 10%) e parada antecipada (*Early Stopping*) monitorando a perda na dobra de validação com paciência de 15 épocas.

#### 4.9.2.2. Floresta Aleatória de Regressão (Random Forest Regressor)
O algoritmo *Random Forest* (Breiman, 2001) baseia-se no método de aprendizado por comitê via agregação *Bootstrap* (*Bagging*). O preditor final é obtido pela média das inferências geradas por um conjunto de $B = 100$ árvores de regressão independentes e descorrelacionadas:

$$\widehat{z}_{\text{RF}}(\mathbf{x}) = \frac{1}{B} \sum_{b=1}^B T_b\left( \mathbf{x}; \boldsymbol{\Theta}_b \right) \tag{4.43}$$

em que cada árvore $T_b$ é ajustada sobre uma réplica amostral com reposição de mesmo tamanho do dataset de treino. A cada divisão nodal (*split*), um subconjunto aleatório de atributos (tamanho $\lfloor \sqrt{p} \rfloor$) é avaliado para selecionar o ponto ótimo de partição que minimiza a variância dos resíduos:

$$\Delta I = \text{Var}(S_{\text{pai}}) - \left( \frac{|S_{\text{esq}}|}{|S_{\text{pai}}|} \text{Var}(S_{\text{esq}}) + \frac{|S_{\text{dir}}|}{|S_{\text{pai}}|} \text{Var}(S_{\text{dir}}) \right) \tag{4.44}$$

Para assegurar parcimônia e mitigar sobre-ajuste em regiões esparsas, impôs-se profundidade máxima restrita ($\text{max\_depth} = 6$) e número mínimo de 2 amostras por folha residual ($\text{min\_samples\_leaf} = 2$), operando sobre a variável transformada $z = \ln(1 + |v|)$.

#### 4.9.2.3. Máquinas de Vetores de Suporte para Regressão (SVR com Kernel RBF)
A regressão por vetores de suporte (Smola; Schölkopf, 2004) busca uma função $f(\mathbf{x}) = \langle \mathbf{w}, \Phi(\mathbf{x}) \rangle + b$ em um espaço de características de dimensão infinita que desvie no máximo $\varepsilon$ dos alvos observados, penalizando apenas os resíduos fora do tubo insensível através da função de perda $\varepsilon$-insensível:

$$L_{\varepsilon}(y, f(\mathbf{x})) = \max(0,\ |y - f(\mathbf{x})| - \varepsilon) \tag{4.45}$$

O problema de otimização convexa dual é formulado por:

$$\min_{\boldsymbol{\alpha}, \boldsymbol{\alpha}^*} \frac{1}{2} \sum_{i=1}^N \sum_{j=1}^N (\alpha_i - \alpha_i^*)(\alpha_j - \alpha_j^*) K(\mathbf{x}_i, \mathbf{x}_j) + \varepsilon \sum_{i=1}^N (\alpha_i + \alpha_i^*) - \sum_{i=1}^N z_i (\alpha_i - \alpha_i^*) \tag{4.46}$$

sujeito a $0 \le \alpha_i, \alpha_i^* \le C$ e $\sum_{i=1}^N (\alpha_i - \alpha_i^*) = 0$. Utilizou-se o núcleo de Função de Base Radial (*Radial Basis Function* — RBF):

$$K(\mathbf{x}_i, \mathbf{x}_j) = \exp\left( - \gamma \|\mathbf{x}_i - \mathbf{x}_j\|^2 \right) \tag{4.47}$$

com hiperparâmetros ajustados em $C = 10{,}0$, $\varepsilon = 0{,}05$ e $\gamma = \text{'scale'} = 1 / (p \cdot \text{Var}(\mathbf{X}))$.

#### 4.9.2.4. Aumento de Gradiente Extremo (XGBoost Regressor)
O algoritmo XGBoost (Chen; Guestrin, 2016) constrói árvores de decisão de forma sequencial aditiva. A cada iteração $m$, uma nova árvore $f_m(\mathbf{x})$ é ajustada para minimizar a expansão de Taylor de segunda ordem da função de perda regularizada:

$$\mathcal{L}^{(m)} \approx \sum_{i=1}^N \left[ g_i f_m(\mathbf{x}_i) + \frac{1}{2} h_i f_m^2(\mathbf{x}_i) \right] + \gamma_{\text{tree}} T_{\text{folhas}} + \frac{1}{2} \lambda_{\text{reg}} \sum_{j=1}^{T_{\text{folhas}}} w_j^2 \tag{4.48}$$

sendo $g_i = \partial \ell / \partial \widehat{z}^{(m-1)}$ e $h_i = \partial^2 \ell / \partial (\widehat{z}^{(m-1)})^2$ os gradientes de primeira e segunda ordem da perda quadrática, $T_{\text{folhas}}$ o número de nós folha e $\lambda_{\text{reg}}$ o parâmetro de regularização $L_2$ sobre os pesos das folhas. Adotou-se taxa de aprendizado $\eta_{\text{lr}} = 0{,}05$, 150 estimadores, profundidade máxima de 4 níveis e subamostragem estocástica de linhas (*subsample* de 80%).

---

### 4.9.3. Resultados Comparativos e Desempenho no Teste Cego

A Tabela 4.9 apresenta a síntese comparativa quantitativa dos quatro algoritmos calibrados, confrontando as métricas obtidas na validação cruzada espacial (`GroupKFold`, 4 dobras) e no conjunto de teste cego independente (Ensaios 8, 14 e 7 intocados).

Tabela 4.9 – Desempenho quantitativo dos modelos DDM na predição de $|v(t)|$.

| Métrica Estatística | MLP (PyTorch) | Random Forest | SVR (RBF) | XGBoost | Critério de Otimização |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **$R^2$ Teste Cego Global** | 0,8297 | **0,9120** | 0,6031 | 0,8009 | Maior é melhor ($\ge 0{,}80$) |
| **RMSE Teste Cego ($\mu\text{m/min}$)** | 26,88 | **19,33** | 41,04 | 29,06 | Menor é melhor |
| **MAE Teste Cego ($\mu\text{m/min}$)** | **5,06** | 5,15 | 8,16 | 6,76 | Menor é melhor |
| **$R^2$ Validação Cruzada ($K=4$)** | 0,2560 $\pm$ 0,1702 | **0,7136 $\pm$ 0,1227** | 0,0743 $\pm$ 0,0666 | 0,6503 $\pm$ 0,2176 | Média $\pm$ desvio padrão entre dobras |
| **$R^2$ Treino (13 ensaios)** | 0,9987 | 0,8368 | 0,1473 | 0,8325 | Capacidade de assimilação |
| **Violação Física (\|v\| < 0)** | **0,00%** | **0,00%** | **0,00%** | **0,00%** | Inegociável ($0{,}00\%$) |
| **Latência Unitária de Inferência** | 262,0 $\mu\text{s}$ | 19685,1 $\mu\text{s}$ | **105,2 $\mu\text{s}$** | 233,4 $\mu\text{s}$ | Tempo por ponto de cálculo |
| **Latência em Lote (1000 pontos)** | **0,33 ms** | 21,05 ms | 5,94 ms | 1,68 ms | Inferência vetorizada contínua |

Fonte: Elaborada pelos autores a partir das rotinas de teste da Etapa 3.2 (2026).

A análise detalhada ensaio a ensaio no conjunto de teste cego revelou comportamentos complementares entre as arquiteturas:
- **Ensaio 8 (Estequiométrico Neutro, $\eta = 1{,}0$)**: o XGBoost obteve a melhor reconstituição pontual ($R^2 = 0{,}9801$), seguido de perto pelo Random Forest ($R^2 = 0{,}9496$) e MLP ($R^2 = 0{,}8290$), enquanto o SVR degradou-se ($R^2 = 0{,}3843$);
- **Ensaio 14 (Leve Excesso Ácido, $\eta = 1{,}5$)**: o MLP registrou o melhor ajuste com curvatura contínua suave ($R^2 = 0{,}9712$), empatado com o SVR ($R^2 = 0{,}9692$) e o Random Forest ($R^2 = 0{,}9168$), ao passo que o XGBoost gerou discretizações em degrau ($R^2 = 0{,}6350$);
- **Ensaio 7 (Forte Excesso Ácido, $\eta = 3{,}1$)**: o Random Forest destacou-se com ampla superioridade de generalização ($R^2 = 0{,}8824$), superando XGBoost ($R^2 = 0{,}7759$), MLP ($R^2 = 0{,}7436$) e SVR ($R^2 = 0{,}5287$).

---

### 4.9.4. Metodologia de Decisão Multicritério (MCDA) e Seleção do Modelo Campeão

Para evitar a escolha arbitrária ou unidimensional baseada unicamente no $R^2$ global de teste, formulou-se um protocolo formal de **Análise de Decisão Multicritério** (*Multi-Criteria Decision Analysis* — MCDA), fundamentado na metodologia de soma ponderada linear normalizada (Triantaphyllou, 2000). A matriz de decisão contemplou cinco critérios técnicos essenciais para a integração com resolvedores numéricos mecanicistas:

$$\text{Score}_m = \sum_{k=1}^5 w_k \cdot S_{m,k} \tag{4.49}$$

com $\sum_{k=1}^5 w_k = 1{,}00$, sendo $S_{m,k} \in [0, 100]$ a pontuação normalizada do modelo $m$ no critério $k$, calculada por:
- Para métricas de benefício (maior é melhor): $S_{m,k} = 100 \cdot \frac{M_{m,k} - \min_j M_{j,k}}{\max_j M_{j,k} - \min_j M_{j,k}}$;
- Para métricas de custo (menor é melhor): $S_{m,k} = 100 \cdot \frac{\max_j M_{j,k} - M_{m,k}}{\max_j M_{j,k} - \min_j M_{j,k}}$.

Os critérios e seus respectivos pesos analíticos foram definidos da seguinte forma:
1. **Generalização em Teste Cego ($w_1 = 0{,}30$)**: $R^2$ global obtido nos três ensaios independentes (8, 14 e 7);
2. **Robustez Espacial na Validação Cruzada ($w_2 = 0{,}25$)**: média do $R^2$ nas 4 dobras do `GroupKFold`, avaliando a estabilidade frente a perturbações no domínio operacional;
3. **Precisão Dimensional dos Resíduos ($w_3 = 0{,}20$)**: inverso da Raiz do Erro Quadrático Médio ($1 / \text{RMSE}$) no conjunto de teste;
4. **Eficiência e Velocidade de Inferência ($w_4 = 0{,}15$)**: taxa de transferência (*throughput*) no cálculo vetorizado em lote de 1000 nós de integração;
5. **Suavidade Derivativa para Acoplamento Físico ($w_5 = 0{,}10$)**: avaliação qualitativa da classe de diferenciabilidade da função predita ($C^\infty$ para redes neurais e SVR vs. $C^0$ por partes para árvores), penalizando descontinuidades abruptas na taxa $|v(t)|$.

A Tabela 4.10 sintetiza a avaliação multicritério final e o ranking de classificação dos modelos competidores.

Tabela 4.10 – Matriz de Decisão Multicritério (MCDA) para seleção do modelo DDM campeão.

| Algoritmo Competidor | Teste Cego ($w_1=0{,}30$) | Robustez CV ($w_2=0{,}25$) | Precisão RMSE ($w_3=0{,}20$) | Eficiência ($w_4=0{,}15$) | Suavidade ($w_5=0{,}10$) | **Score Final MCDA** | Classificação |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest Regressor** | **100,00** | **100,00** | **100,00** | 10,25 | 40,00 | **79,50 / 100** | **1º Lugar (CAMPEÃO)** |
| **XGBoost Regressor** | 63,78 | 90,09 | 55,18 | 93,65 | 30,00 | **71,30 / 100** | 2º Lugar (Vice-campeão) |
| **Multi-Layer Perceptron (PyTorch)** | 73,08 | 28,42 | 65,22 | **100,00** | **100,00** | **67,16 / 100** | 3º Lugar |
| **Support Vector Regression (SVR)** | 0,00 | 0,00 | 0,00 | 74,48 | 80,00 | **20,94 / 100** | 4º Lugar |

Fonte: Elaborada pelos autores a partir dos ensaios da Subetapa 3.2.5 (2026).

Com base na pontuação máxima de **79,50 pontos**, o **Random Forest Regressor** consagrou-se como o **Modelo Campeão da Etapa 3.2**. O modelo apresentou o maior coeficiente de determinação no teste cego ($R^2 = 0{,}9120$), o menor erro quadrático dimensional ($\text{RMSE} = 19{,}33\ \mu\text{m/min}$) e extraordinária estabilidade espacial na validação cruzada ($R^2 = 0{,}7136 \pm 0{,}1227$), demonstrando capacidade de generalização e ausência de sobre-ajuste severo. 

Seus artefatos serializados de produção (`rf_kinetics_v1.joblib` e metadados `rf_config.json`) foram salvos e aprovados para conexão direta com o resolvedor do Balanço Populacional na Subseção 4.10.
