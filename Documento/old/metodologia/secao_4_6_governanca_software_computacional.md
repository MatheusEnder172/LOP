## 4.6. Implementação Computacional, Arquitetura de Software e Governança

Nesta subseção são detalhadas a infraestrutura computacional, a arquitetura modular orientada a objetos, os padrões de engenharia de software (*Clean Code* e princípios SOLID), os protocolos de governança e rastreabilidade metrológica, a suíte de testes unitários automatizados e os critérios de padronização visual adotados em todo o desenvolvimento da modelagem híbrida. O estabelecimento desse arcabouço computacional garante a integridade termodinâmica, a robustez numérica e a total reprodutibilidade científica das simulações mecanicistas e dos modelos de aprendizado de máquinas implementados nas etapas subsequentes.

---

### 4.6.1. Linguagem de Programação e Ecossistema Científico

Todo o pipeline computacional do projeto foi desenvolvido na linguagem de programação Python (versão 3.10+), selecionada pela robustez de seu ecossistema científico, facilidade de interoperabilidade entre resolvedores diferenciais e bibliotecas de aprendizado de máquinas (*Machine Learning* — ML), além de seu amplo suporte à vetorização e paralelismo em arrays multidimensionais (Van Rossum; Drake, 2009; Harris et al., 2020).

A Tabela 4.6 sintetiza os principais pacotes e bibliotecas científicas especializadas empregadas no ambiente de desenvolvimento, categorizadas segundo sua função no fluxo de modelagem.

Tabela 4.6 – Ecossistema computacional e bibliotecas especializadas utilizadas no projeto.

| Categoria | Biblioteca / Pacote | Versão Mínima | Função Primária no Projeto |
| :--- | :--- | :---: | :--- |
| **Computação Numérica** | `numpy` | 1.24+ | Vetorização de malhas de tamanho de partícula, álgebra linear e cálculo de tensores |
| **Integração e Otimização** | `scipy` | 1.10+ | Integração numérica por quadratura adaptativa (`scipy.integrate.quad`), interpolação cúbica contínua e algoritmos de otimização quase-Newton (`scipy.optimize.minimize`, método L-BFGS-B) |
| **Estruturação de Dados** | `pandas` | 2.0+ | Manipulação de DataFrames relacionais, agregação de séries temporais de bancada e rastreamento metrológico |
| **Aprendizado de Máquinas** | `scikit-learn` | 1.3+ | Pré-processamento, escalonamento (`StandardScaler`), validação cruzada espacial (`GroupKFold`), modelos clássicos (`RandomForestRegressor`, `SVR`) e métricas de erro |
| **Gradient Boosting** | `xgboost` | 1.7+ | Treinamento de comitês sequenciais de árvores de decisão com regularização avançada |
| **Deep Learning** | `torch` (PyTorch) | 2.0+ | Concepção, treino e diferenciação automática do regressor neural profundo *Multi-Layer Perceptron* (MLP) |
| **Visualização Científica** | `matplotlib` / `seaborn` | 3.7+ / 0.12+ | Renderização de gráficos de alta resolução (300 DPI) e figuras vetoriais comparativas |
| **Garantia de Qualidade** | `pytest` | 7.4+ | Execução automatizada da suíte de testes de regressão, limites físicos e conservação de massa |
| **Persistência de Modelos** | `joblib` | 1.3+ | Serialização de hiperparâmetros, pesos de modelos ajustados e transformadores estatísticos |

Fonte: Elaborada pelos autores (2026).

---

### 4.6.2. Arquitetura Modular e Princípios de Engenharia de Software (SOLID)

Para evitar a criação de códigos monolíticos de difícil depuração, manutenção ou acoplamento espúrio entre física e dados, adotou-se uma arquitetura estritamente modular e orientada a objetos (Martin, 2017). O código-fonte foi estruturado sob o diretório raiz `Código/src/`, particionado em quatro módulos de responsabilidade única:

1. **Módulo Fenomenológico (`src/physics/`)**: 
   Contém os algoritmos analíticos e mecanicistas puros do processo de lixiviação:
   - `granulometry.py`: encapsula a classe `RosinRammlerGranulometry`, responsável pela avaliação contínua da função densidade de distribuição $f_0(D)$, cálculo analítico e numérico dos momentos volumétricos da população e discretização log-espaçada da malha de partículas;
   - `kinetics.py`: implementa a classe `DissolutionKinetics`, que computa a taxa de retração interfacial $|v(t)|$ do Modelo do Núcleo em Diminuição (SCM), a imposição da acidez crítica de parada, o amortecimento empírico $\alpha$ e o balanço estequiométrico de solvente livre ($C_{Af}$);
   - `pbm_batch.py`: abriga o resolvedor numérico `BatchPBMSolver`, que processa a Equação Diferencial Parcial do Balanço Populacional em batelada pelo Método das Características (MOC), gerando os perfis temporais de conversão de zinco $X_{\text{Zn}}(t)$ e concentração de ácido livre $C_{Af}(t)$.
2. **Módulo Orientado por Dados (`src/ml/`)**:
   Reúne os componentes de pré-processamento, engenharia de atributos e treinamento supervisionado:
   - `preprocessing.py`: executa a partição espacial estratificada (85/15), ajuste de transformadores estatísticos exclusivamente no conjunto de calibração e aplicação da função $\ln(1 + |v|)$ para garantia de não-negatividade;
   - `mlp.py`: define a arquitetura da rede neural artificial profunda *Multi-Layer Perceptron* em PyTorch, incluindo normalização em lote (*Batch Normalization*), regularização por abandono estocástico (*Dropout*) e rotina de parada antecipada (*Early Stopping*);
   - Submódulos dedicados à calibração, sintonia de hiperparâmetros e persistência serializada dos modelos Random Forest, SVR e XGBoost.
3. **Módulo de Acoplamento Híbrido (`src/hybrid/`)**:
   - `serial_hybrid.py`: classe permanente `SerialHybridModel`, que operacionaliza a orquestração serial entre o preditor de aprendizado de máquinas (que infere a cinética interfacial $|v(t)|$) e o resolvedor de primeiros princípios (`BatchPBMSolver`), aplicando internamente malhas temporais ultrafinas de quadratura e filtros de projeção física de conservação de massa.
4. **Módulo de Utilitários Transversais (`src/utils/`)**:
   - `metrics.py`: padroniza as funções de cálculo do coeficiente de determinação ($R^2$), raiz do erro quadrático médio (RMSE), erro médio absoluto (MAE), erro residual máximo e matriz de ganho relativo;
   - `plotting.py`: estabelece o estilo gráfico unificado, paletas de cores acessíveis, escalas tipográficas e parâmetros de renderização vetorial.

A conformidade com as boas práticas de engenharia de software foi regida pelos seguintes princípios:
- **Princípio da Responsabilidade Única (*Single Responsibility Principle* — SRP)**: cada classe ou função possui um escopo exclusivo e bem definido, garantindo que alterações na formulação cinética não afetem o resolvedor do balanço populacional nem a rotina de treinamento dos modelos de aprendizado de máquina;
- **Princípio do Aberto/Fechado (*Open/Closed Principle* — OCP)**: a classe `SerialHybridModel` foi projetada para permitir a integração imediata de novos algoritmos de regressão sem requerer qualquer alteração na mecânica de integração temporal ou na lógica de conservação estequiométrica;
- **Princípio da Inversão de Dependência (*Dependency Inversion Principle* — DIP)**: o acoplamento híbrido depende de uma interface comum de inferência (`predict`), tornando o resolvedor físico desacoplado das idiossincrasias de implementação interna de bibliotecas externas (como PyTorch ou Scikit-Learn);
- **Legibilidade e Tipagem Estática (*Type Hints*)**: todas as rotinas e métodos públicos foram anotados com tipos estáticos de entrada e saída (conforme a PEP 484) e acompanhados de documentação técnica (*docstrings* no padrão Google), detalhando as hipóteses termodinâmicas, unidades de medida e potenciais exceções numéricas.

---

### 4.6.3. Governança de Dados, Rastreabilidade e Reprodutibilidade

Para garantir total auditabilidade e reprodutibilidade metrológica em conformidade com as diretrizes acadêmicas da UFMG e da literatura hidrometalúrgica, o projeto estabeleceu um protocolo de governança estruturado em três pilares:

1. **Rastreabilidade de Dados Primários (`RASTREABILIDADE_DADOS.md`)**:
   Cada valor numérico experimental utilizado — abrangendo diâmetros característicos, composições químicas da calcina, concentrações iniciais de ácido, massas alimentadas, tempos de amostragem e conversões de bancada — foi formalmente indexado a uma fonte primária na dissertação de mestrado de Bortot Coelho (2017) ou na tese de doutorado de Balarini (2009). O documento de rastreabilidade explicita o número do capítulo, número da tabela original e número de página de cada ponto de dados, assegurando a verificação cruzada imediata.
2. **Diário de Desenvolvimento Contínuo (`DEVLOG.md`)**:
   Todas as implementações computacionais, alterações de algoritmos, decisões de modelagem e investigações de anomalias numéricas foram registradas cronologicamente em um repositório central de governança (`DEVLOG.md`). Para cada atividade, registram-se:
   - Data, hora e escopo da intervenção;
   - Hipótese físico-química ou decisão algorítmica subjacente;
   - Resultados quantitativos e métricas de desempenho obtidas ($R^2$, RMSE, MAE, tempos de convergência);
   - Falhas ou desvios numéricos identificados e justificativas técnicas das ações corretivas adotadas.
3. **Política de Preservação e Depreciação de Dados**:
   Estabeleceu-se uma política estrita de não-exclusão definitiva de artefatos gerados. Caso uma rotina, modelo ou figura precise ser substituído em virtude de refinamento metodológico, o arquivo original é mantido e transferido para um subdiretório denominado `old/`, acompanhado de registro documental formal no `DEVLOG.md` descrevendo o motivo da descontinuação e o artefato sucessor.

---

### 4.6.4. Protocolo de Validação Computacional e Testes Automatizados

Com a finalidade de assegurar que nenhuma modificação no código introduzisse erros de regressão ou violasse princípios termodinâmicos fundamentais, foi implementada uma suíte abrangente de testes unitários e de integração automatizados por meio do arcabouço `pytest`.

A suíte completa totaliza **61 testes unitários independentes**, distribuídos em todas as etapas da cadeia de modelagem:
- **Testes de Consistência Física e Conservação de Massa**:
  - Restrição de conversão fracionária: $X_{\text{Zn}}(t) \in [0, 1]$ para qualquer instante temporal e condição operacional;
  - Teto de estequiometria em meio limitante: $X_{\text{Zn}}(t) \le \eta$ para $\eta < 1,0$;
  - Não-negatividade da concentração de ácido livre: $C_{Af}(t) \ge 0\ \text{mol}\cdot\text{L}^{-1}$;
  - Projeção de não-crescimento: $v(t) \le 0$ e taxa em módulo $|v(t)| \ge 0$, garantindo que a retração cumulativa $\delta(t)$ seja estritamente monótona não-decrescente ($d\delta/dt \ge 0$);
- **Testes de Integridade Numérica e Comportamento Assintótico**:
  - Verificação de ausência de indefinições numéricas (`NaN` ou `Inf`) em regimes limites ($t \to 0$, $t \to \infty$ ou $C_{Af} \to 0$);
  - Conservação do volume total da população particulada na malha contínua do PBM ($M_3(0) \approx 1$ e divergência nula de massa);
  - Exatidão da quadratura adaptativa de $\delta(t)$ frente à solução analítica conhecida em regimes de velocidade constante ou bi-exponencial;
- **Testes de Blindagem Metodológica de Aprendizado de Máquinas**:
  - Verificação estrita de ausência de vazamento de dados (*data leakage*): assegura-se que os parâmetros dos transformadores estatísticos (`StandardScaler`) sejam computados unicamente a partir do conjunto de calibração;
  - Preservação integral do envoltório convexo (*Convex Hull*): teste automatizado garantindo que os extremos da matriz experimental ($C_{A0} \in \{0,10; 1,50\}\ \text{mol/L}$ e $\eta \in \{0,5; 3,1\}$) residam no conjunto de treino.

A execução bem-sucedida de 100% dos testes da suíte (61/61 aprovados) antes de cada etapa de simulação constituiu critério obrigatório de aceitação e avanço no projeto.

---

### 4.6.5. Padrão Estético e Critérios de Visualização Científica

A comunicação visual dos resultados numéricos e experimentais foi padronizada segundo diretrizes rigorosas de publicação científica internacional (Tufte, 2001; Rougier; Droettboom; Bourne, 2014):

1. **Resolução e Formato de Exportação**:
   Todas as figuras foram geradas na resolução mínima de **300 DPI** no formato matricial `.png` e exportadas concomitantemente em formato vetorial `.pdf`, garantindo nitidez tipográfica e escalabilidade sem distorção para inclusão em documentos técnicos e apresentações acadêmicas;
2. **Hierarquia Tipográfica e Legibilidade**:
   Padronizou-se o emprego de fontes sem serifa legíveis em tamanhos proporcionais (rótulos de eixos em 11–12 pt, títulos de subplots em 12–13 pt e marcações de escala numérica em 9–10 pt). Todos os rótulos de eixos contêm obrigatoriamente a grandeza física e sua unidade formal expressa entre parênteses ou colchetes (por exemplo, $X_{\text{Zn}}\ [-]$, $C_{Af}\ [\text{mol/L}]$, $t\ [\text{min}]$, $|v|\ [\mu\text{m/min}]$);
3. **Diferenciação Estilística entre Experimento e Modelo**:
   Para eliminar qualquer ambiguidade de interpretação:
   - **Dados experimentais**: representados exclusivamente por marcadores discretos pontuais com preenchimento colorido e barras de erro correspondentes ao desvio padrão amostral da triplicata de bancada;
   - **Modelos fenomenológicos e híbridos**: representados por linhas contínuas ou tracejadas suaves, sem marcadores discretos sobrepostos, calculadas sobre malhas temporais finas e regulares;
4. **Paletas Cromáticas Acessíveis e de Alto Contraste**:
   Adotou-se o esquema cromático *Colorblind-Friendly* (como as paletas *Set1*, *Dark2* e gradientes perceptuais uniformes *Viridis* e *Cividis*), garantindo distinção inequívoca entre as curvas mesmo em impressões monocromáticas ou para leitores com deficiências de visão cromática.
