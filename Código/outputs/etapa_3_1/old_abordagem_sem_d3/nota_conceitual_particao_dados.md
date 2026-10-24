# Nota Conceitual — Partição de Dados e Prevenção de Vazamento em Cinéticas Químicas

**Projeto**: Modelagem Híbrida Serial de Lixiviação de Zinco (DEQ/UFMG)  
**Autor**: Antigravity AI Pair Programmer & Equipe LOP  
**Data**: 25 de Setembro de 2026  

---

## 1. O Dilema do Particionamento em Séries Temporais de Processos Químicos

No aprendizado de máquina supervisionado padrão para dados tabulares, a prática comum consiste em embaralhar todas as linhas da tabela e dividi-las aleatoriamente em conjuntos de treino e teste (ex.: 80% treino / 20% teste via `train_test_split`).

Em cinéticas heterogêneas e processos químicos em batelada, **aplicar uma divisão aleatória de amostras individuais é um erro metodológico grave**, conhecido na literatura como **Vazamento Temporal de Dados (*Temporal Data Leakage*)**:
1. **Autocorrelação Temporal Contínua**: Se um modelo preditivo receber para treinamento os pontos de t = 0,5 min e t = 2,0 min de um dado ensaio, e o ponto de t = 1,0 min for colocado no conjunto de teste, o modelo não estará aprendendo a generalizar o comportamento fenomenológico do sistema físico-químico; estará apenas executando uma interpolação trivial entre pontos vizinhos fortemente correlacionados.
2. **Superestimação de Desempenho**: Esse tipo de vazamento produz métricas de validação artificialmente perfeitas (R² > 0,999) durante a modelagem em laboratório, mas que colapsam catastroficamente quando o modelo é submetido a um novo reator ou a uma nova condição operacional não vista.

Para garantir validade científica rigorosa, a partição deve ocorrer estritamente ao nível de **ensaio experimental (*Batch-Level Split*)**: todos os instantes temporais de um ensaio pertencem exclusivamente ao Treino ou exclusivamente ao Teste Cego.

---

## 2. A Estratégia de Partição 85/15: Seleção dos Ensaios de Teste Cego

Dispondo de 16 ensaios de bancada representados por uma matriz fatorial 4×4 em termos de concentração inicial de ácido sulfúrico (C_A0 = 0,10; 0,50; 1,00; 1,50 mol/L) e razão molar estequiométrica (η = 0,5; 1,0; 1,5; 3,1), adotou-se a divisão 13/3 (81,25% treino / 18,75% teste cego).

A seleção dos 3 ensaios de teste cego (**Ensaios 7, 8 e 14**) foi guiada por três princípios fundamentais de engenharia química e aprendizado estatístico:

### A. Preservação do Envoltório Convexo (*Convex Hull*)
Modelos orientados exclusivamente por dados, sobretudo algoritmos baseados em árvores de decisão (como Random Forest e XGBoost), possuem baixa capacidade de extrapolação fora dos limites dos hipercubos nos quais foram treinados. Eles projetam predições constantes para além do menor e maior valor de cada feature.

Por essa razão, **todos os 4 vértices do domínio experimental** foram mantidos obrigatoriamente no conjunto de treino:
- Vértice 1: Ensaio 1 (C_A0 = 0,10 mol/L, η = 0,5) — Mínimo de ácido, mínimo de estequiometria.
- Vértice 2: Ensaio 2 (C_A0 = 0,10 mol/L, η = 3,1) — Mínimo de ácido, máximo de estequiometria.
- Vértice 3: Ensaio 5 (C_A0 = 1,50 mol/L, η = 0,5) — Máximo de ácido, mínimo de estequiometria.
- Vértice 4: Ensaio 16 (C_A0 = 1,50 mol/L, η = 3,1) — Máximo de ácido, máximo de estequiometria.

Com isso, o conjunto de teste cego avalia a capacidade de **interpolação pura** da Inteligência Artificial em pontos intermediários da malha operacional, garantindo uma avaliação não tendenciosa.

### B. Cobertura dos Regimes Físico-Químicos em Padrão "Tabuleiro de Xadrez"
Os 3 ensaios selecionados para o teste cego cobrem as três grandes classes hidrometalúrgicas da lixiviação de zinco:
1. **Ensaio 8 (C_A0 = 0,50 mol/L, η = 1,0)**: Regime estequiométrico estrito. Apresenta esgotamento progressivo do ácido e estabilização incompleta da conversão em torno de X_Zn ≈ 87%.
2. **Ensaio 14 (C_A0 = 1,00 mol/L, η = 1,5)**: Regime de leve excesso estequiométrico. Transição para extração elevada (X_Zn ≈ 97%) com cinética moderada.
3. **Ensaio 7 (C_A0 = 0,50 mol/L, η = 3,1)**: Regime de forte excesso de ácido. Dissolução acelerada com conversão atingindo 100% antes do término do ensaio.

Essa alternância espacial (em tabuleiro de xadrez) impede que dois ensaios vizinhos imediatos sejam retirados simultaneamente, evitando zonas esparsas no treino.

### C. Ancoragem Termodinâmica de η = 0,5
Na razão molar deficitária (η = 0,5), a quantidade de ácido alimentada é estequiometricamente insuficiente para dissolver mais de 50% da zincita presente (ZnO + H₂SO₄ → ZnSO₄ + H₂O).
Nesse regime, a taxa de dissolução v(t) sofre uma desaceleração abrupta e cai a zero por esgotamento de H⁺. Para que os modelos de aprendizado de máquina aprendam com fidelidade a curva de corte assintótico e o patamar de conversão limite termodinâmico, **todos os 4 ensaios de η = 0,5 (Ensaios 1, 3, 4 e 5) foram preservados no treino**.

---

## 3. Validação Cruzada por Grupos (`GroupKFold` — 4 Dobras)

Durante a calibração de hiperparâmetros (busca em grade ou otimização bayesiana) na Etapa 3.2, o particionamento tripartite tradicional (ex.: 10 treino / 3 validação / 3 teste) reduziria excessivamente a base de ajuste primária para apenas 10 ensaios.

Para contornar essa limitação sem introduzir vazamento de dados, adotou-se o algoritmo **`GroupKFold` com 4 dobras** aplicado exclusivamente sobre os 13 ensaios de treino:
- O agrupamento é parametrizado pelo identificador do ensaio (`ensaio`).
- Em cada dobra de validação cruzada, 3 ou 4 ensaios inteiros são reservados como subconjunto de validação, enquanto os 9 ou 10 ensaios restantes atuam no ajuste dos pesos dos modelos.
- Esse procedimento rotaciona os dados 4 vezes, assegurando que 100% dos 13 ensaios de treino participem do processo de validação, sem que nenhum nó temporal do mesmo ensaio seja compartilhado entre treino e validação.

---

## 4. Normalização Estatística e Tratamento de Variância Neutra

Para permitir a convergência estável de redes neurais artificiais (Multi-Layer Perceptron — MLP) e métodos baseados em vetores de suporte (Support Vector Regression — SVR), os dados de entrada e saída foram padronizados via `StandardScaler` (média nula e variância unitária):

z = (x - μ) / σ

### Regras de Governança dos Transformadores:
1. **Ajuste Exclusivo no Treino**: Os parâmetros μ e σ foram calculados unicamente a partir das 793 amostras densas do conjunto de treino. Aplicar `fit` sobre todo o dataset ou sobre o conjunto de teste violaria a premissa de teste cego.
2. **Tratamento da Temperatura Isotérmica**: Nos ensaios de bancada de Bortot Coelho (2017), a temperatura foi mantida constante em 40,0 °C (desvio-padrão nulo, σ = 0). Para evitar divisões por zero ou valores indeterminados (NaN), o pré-processador atribui escala unitária neutra (σ = 1,0, μ = 40,0) à coluna de temperatura. Isso mantém a coluna normalizada em z = 0, assegurando compatibilidade estrutural com a Fase 6 (planta piloto), onde a temperatura é variável.
3. **Persistência de Objetos**: Os transformadores ajustados foram serializados no arquivo `scalers.joblib`, permitindo a reversibilidade exata das predições de v(t) da escala padronizada para a unidade física original (µm/min).
