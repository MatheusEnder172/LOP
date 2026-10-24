# 4. MATERIAIS E MÉTODOS: MODELAGEM HÍBRIDA SERIAL COM MACHINE LEARNING APLICADA À LIXIVIAÇÃO DE CONCENTRADO USTULADO DE ZINCO

**Autores**: Daniel Couto Vieira, Guilherme Moura de Sousa Franco, Matheus Henrique Borba Póvoas, Rodrigo Amaral da Mata  
**Orientador**: Prof. Dr. Fabrício Bortot Coelho  
**Instituição**: Departamento de Engenharia Química — Universidade Federal de Minas Gerais (DEQ/UFMG)  
**Ano**: 2026  

---

## 4.1. Visão Geral e Estrutura Metodológica

O presente trabalho desenvolve, calibra e valida uma metodologia de modelagem híbrida serial (*Grey-Box Serial*) para a predição da cinética de lixiviação ácida de calcina de zinco (concentrado ustulado de esfalerita) em reatores industriais e de bancada operados em batelada e batelada alimentada.

O desafio central enfrentado pela modelagem mecanicista clássica baseada em primeiros princípios (*White-Box*) reside no fato de que sistemas heterogêneos minerais apresentam severas não-idealidades físico-químicas:
1. Ampla polidispersão de tamanhos de partícula abrangendo quase três ordens de grandeza (0,45 µm a 300 µm);
2. Retardo cinético pronunciado nas etapas intermediárias e tardias da dissolução, decorrente do aumento da força iônica, elevação da viscosidade do licor lixiviante, efeito do íon comum (acúmulo de Zn²⁺ e Fe²⁺/Fe³⁺) e formação de microcamadas passivantes residuais de sílica amorfa e ferritas insolúveis;
3. Inadequação das correlações semi-empíricas estáticas com parâmetros fixos (como o parâmetro cinético de retardamento α de Bortot Coelho, 2017) para prever a cinética sob condições operacionais variáveis de razão molar ácido/minério e acidez livre.

Por outro lado, abordagens puramente orientadas por dados (*Black-Box* ou *Data-Driven Models* — DDM) que tentam mapear diretamente as variáveis de entrada na conversão mássica final sofrem de perda de coerência física: violam a conservação estrita de massa, preveem conversões superiores ao limite estequiométrico máximo imposto pela quantidade inicial de reagente ácido lixiviante e falham catastroficamente ao extrapolar para fora do domínio experimental estrito de calibração (*Out-of-Distribution* — OOD).

Para superar essas deficiências complementares, este trabalho concebe uma arquitetura híbrida serial (von Stosch et al., 2014; Solle et al., 2017), estruturada em dois módulos cooperativos fundamentais:
- **Módulo Orientado por Dados (Black-Box Protagonista)**: Um regressor baseado em Redes Neurais Artificiais Profundas (*Multi-Layer Perceptron* — MLP em PyTorch com funções de ativação infinitamente diferenciáveis C∞ e normalização por camadas LayerNorm) é empregado para aprender a lei constitutiva complexa da taxa de retração interfacial linear instantânea das partículas (|v(t)| = |dD/dt| em µm/min), a partir das variáveis operacionais do processo;
- **Módulo Mecanicista de Primeiros Princípios (White-Box)**: A taxa |v(t)| estimada pela rede neural é integrada no tempo pelo operador de retração cumulativa δ(t) e injetada no resolvedor numérico da Equação do Balanço Populacional (*Population Balance Model* — PBM), convoluindo analiticamente a distribuição de tamanhos com a lei de retração e calculando a evolução do momento volumétrico de terceira ordem M_3(t). A conservação estequiométrica de reagentes líquidos e sólidos é estritamente garantida pelo Balanço de Massa em Batelada de Herbst (1979).

O fluxo metodológico do trabalho organiza-se em nove etapas sequenciais interligadas, descritas minuciosamente ao longo deste capítulo e ilustradas no fluxograma conceitual da Figura 4.1:

```
[Bancada Experimental (Bortot Coelho, 2017)]
         │
         ▼
[Caracterização Física, Química e Granulométrica (RRB)]
         │
         ▼
[Dedução Rigorosa da Distribuição Numérica (RRB ÷ D³)] ──► Eliminação de α (α = 0)
         │
         ▼
[Condição Inicial Física Hardcoded em t = 0 (X_Zn=0, δ=0)] ──► Exclusão de t = 0 dos Modelos
         │
         ▼
[Otimização Inversa Bi-Exponencial dos Alvos Cinéticos |v(t)|] (t > 0, 3 Variáveis: [C_A0, η, t])
         │
         ▼
[Treinamento e Benchmark dos Regressores DDM: MLP, RF, SVR, XGBoost]
         │
         ▼
[Seleção Multicritério MCDA: MLP Campeão C∞ + Autograd (Score: 92,84)]
         │
         ▼
[Acoplamento Híbrido Serial (MLP C∞ ──► PBM com RRB ÷ D³ ──► Herbst)]
         │
         ▼
[Benchmark In-Domain (16 Ensaios) & Validação Externa OOD (Balarini, 2009: 176 Pontos)]
```

---

## 4.2. Matéria-Prima, Sistema Experimental e Protocolos Analíticos

### 4.2.1. Matéria-Prima e Caracterização da Calcina de Zinco
A matéria-prima investigada neste trabalho é a calcina de zinco (concentrado sulfetado de zinco ustulado), proveniente das operações industriais de ustulação em leito fluidizado da unidade da Nexa Resources localizada em Três Marias (Minas Gerais, Brasil), conforme reportado na dissertação de Bortot Coelho (2017). 

A fim de assegurar a representatividade composicional e granulométrica de cada alíquota experimental utilizada nos ensaios de dissolução, o lote mineral bruto (massa de aproximadamente 15 kg) foi submetido a protocolo de homogeneização mecânica e quarteamento sequencial pelo método da pilha cônica e quarteador de Jones (Luz; Sampaio; França, 2010).

Os procedimentos analíticos instrumentais empregados na caracterização física, mineralógica e química do lote compreenderam:

1. **Picnometria de Líquidos e Hélio**: A densidade real do sólido mineral particulado foi quantificada por picnometria com água desaerada a 25,0 °C em picnômetro calibrado de 50 mL e conferida por picnometria a gás hélio em picnômetro multipicnométrico Micromeritics AccuPyc II 1340. A densidade real média obtida foi de ρ_sol = 5,61 g/cm³. Com base nesse valor e na massa molar da zincita pura (MM_ZnO = 81,38 g/mol), determinou-se a densidade molar da zincita sólida pura:
   ρ_s = (5,61 g/cm³ · 1000 cm³/L) / (81,38 g/mol) = 68,93 ≈ 69,2 mol/L
   Esse parâmetro volumétrico fundamental rege a relação entre retração geométrica interfacial e consumo molar de reagente no Balanço Populacional (Balarini, 2009; Bortot Coelho, 2017);

2. **Difração de Raios X (DRX)**: Conduzida em difratômetro Empyrean (PANalytical) com tubo de emissão de radiação Cu-Kα (comprimento de onda λ = 1,5406 Å), operando sob tensão de 40 kV e corrente de 40 mA, com varredura angular 2θ entre 10° e 80° e passo de 0,02°. O refinamento cristalográfico identificou a presença predominante de:
   - Zincita (óxido de zinco hexagonal, ZnO — fase solúvel majoritária);
   - Franklinita / Ferrita de zinco (ZnFe₂O₄ com estrutura espinélio — fase secundária refratária);
   - Willemita (silicato de zinco, Zn₂SiO₄);
   - Quartzo residual (SiO₂);
   - Esfalerita remanescente não convertida na ustulação (ZnS);

3. **Fluorescência de Raios X (FRX)**: Conduzida em espectrômetro por dispersão de comprimento de onda (FRX-WDS, Philips PW2400) para o inventário semiquantitativo dos cátions majoritários;

4. **Digestão Ácida Total e Espectrofotometria de Absorção Atômica (EAA)**: Para quantificação elementar absoluta, alíquotas de 1,000 g de calcina foram submetidas à dissolução ácida exaustiva em água-régia (mistura concentrada de HCl e HNO₃ na proporção volumétrica 3:1) sob aquecimento contínuo em refluxo durante 120 minutos. Os licores foram filtrados em papel faixa azul, avolumados em balões aferidos de 500 mL e dosados em espectrofotômetro de absorção atômica de chama (EAA, modelo XPlorAA, GBC Scientific Equipment). A análise estabeleceu teores totais de zinco elementar de 61,2% (m/m) e ferro total de 5,8% (m/m);

5. **Lixiviação Seletiva Amoniacal (Método de Elgersma et al., 1992)**: Como as fases de ferrita de zinco (ZnFe₂O₄) e esfalerita (ZnS) são refratárias ao ataque ácido sulfúrico brando a 40 °C, adotou-se o método analítico de lixiviação seletiva em solução alcalina tamponada de carbonato/cloreto de amônio. Alíquotas de calcina foram agitadas a 25 °C por 120 minutos em solução contendo 150 g/L de NH₃ e 20 g/L de NH₄Cl. Sob essas condições de complexação de zinco pelo íon tetraaminzinco [Zn(NH₃)₄]²⁺, apenas a zincita livre (ZnO) se dissolve, mantendo-se a ferrita intacta no resíduo. A dosagem por EAA quantificou que o teor de zincita livre na calcina é de:
   T_ZnO = 76,1% em massa (base seca)
   sendo este o parâmetro estequiométrico que delimita o potencial de solubilização rápida em meio ácido.

---

### 4.2.2. Sistema Experimental de Lixiviação em Batelada
Os ensaios cinéticos descontínuos foram conduzidos no reator cilíndrico de vidro borossilicato encamisado esquematizado por Bortot Coelho (2017), dotado das seguintes especificações técnicas:
- Volume geométrico nominal do reator de 500 mL, operado rigorosamente com volume líquido constante de V = 400 mL (0,400 L) de solução aquosa de ácido sulfúrico (H₂SO₄ P.A., Merck, 98% m/m, diluído em água desionizada);
- Tampa vedada com quatro bocas esmerilhadas destinadas ao eixo de agitação, sensor de temperatura acoplado a termômetro digital calibrado, eletrodo combinado de pH (Denver Instrument, modelo 220) e condensador reto de refluxo com circulação de água gelada para prevenção rigorosa de perdas por evaporação do solvente aquoso;
- Termostatização via camisa externa acoplada a banho ultratermostático microprocessado (modelo Fuzzy, Thermo Fisher Scientific), operando com circulação forçada de água a T = 40,0 °C ± 0,5 °C;
- Agitação mecânica promovida por agitador de bancada digital acoplado a impelidor metálico do tipo turbina de pás planas retas (diâmetro de 35 mm, assentado a um terço da altura líquida em relação ao fundo semiesférico). A velocidade de rotação foi fixada em 1000 rpm (rotações por minuto). Esse nível de agitação situa-se consideravelmente acima da velocidade crítica de suspensão de partículas de Zwietering (N_js ≈ 450 rpm para o sistema avaliado), garantindo operação em regime turbulento pleno e anulando a espessura da camada limite hidrodinâmica externa em torno dos grãos, de modo que a resistência à difusão mássica externa no filme líquido é rigorosamente nula (Balarini, 2009; Bortot Coelho, 2017).

---

### 4.2.3. Planejamento Fatorial Completo 4×4 e Balanço de Carga
Para investigar de modo sistemático o comportamento cinético sob ampla faixa de disponibilidade de lixiviante em relação ao sólido particulado, estabeleceu-se um Planejamento Fatorial Completo 4×4, combinando quatro níveis de concentração inicial de ácido sulfúrico (C_A0) e quatro níveis de razão molar estequiométrica ácido/óxido (η), perfazendo 16 ensaios cinéticos executados em triplicata experimental autêntica (Bortot Coelho, 2017, Apêndice A1.1).

A razão molar estequiométrica η define a proporção entre a quantidade de matéria inicial de ácido sulfúrico na fase líquida (n_A0) e a quantidade de matéria inicial de óxido de zinco solúvel presente na massa de calcina alimentada (n_B0):

```
η = n_A0 / n_B0 = (V · C_A0) / [ (m_B0 · T_ZnO) / MM_ZnO ]
```

onde:
- V: volume líquido da fase aquosa de lixiviação (0,400 L);
- C_A0: concentração molar inicial de H₂SO₄ na solução (mol/L);
- m_B0: massa inicial de calcina sólida adicionada na batelada (g);
- T_ZnO: fração mássica de zincita pura na calcina (0,761);
- MM_ZnO: massa molar da zincita (81,38 g/mol).

Reorganizando a equação para fixar rigorosamente os valores nominais planejados de η, deduz-se a massa necessária de calcina sólida alimentada em cada ensaio:

```
m_B0 = (V · C_A0 · MM_ZnO) / (η · T_ZnO)
```

Os níveis operacionais investigados englobaram:
- Concentração inicial de ácido: C_A0 = 0,10; 0,50; 1,00 e 1,50 mol/L (abrangendo desde condições diluídas até a acidez praticada na lixiviação industrial neutra e ácida de zinco);
- Razão molar estequiométrica: η = 0,5 (deficiência estequiométrica de ácido, reagente limitante); η = 1,0 (condição equimolar 1:1 rigorosamente estequiométrica); η = 1,5 (excesso de reagente de +50%); e η = 3,1 (forte excesso de reagente de +210%).

A Tabela 4.1 sumariza a matriz do planejamento experimental, as massas sólidas introduzidas e as respectivas razões sólido/líquido (densidade de polpa).

**Tabela 4.1 – Matriz do planejamento fatorial completo 4×4 de lixiviação em batelada (Bortot Coelho, 2017).**

| Ensaio | C_A0 (mol/L) | Razão Molar η (-) | m_B0 (g) | Densidade Sólidos (g/L) | Regime Estequiométrico |
|:------:|:------------:|:-----------------:|:--------:|:-----------------------:|:-----------------------|
| **01** | 0,10 | 0,5 | 8,6 | 21,4 | Deficiência ácida (limitante) |
| **02** | 0,50 | 0,5 | 42,8 | 106,9 | Deficiência ácida (limitante) |
| **03** | 1,00 | 0,5 | 85,6 | 213,9 | Deficiência ácida (limitante) |
| **04** | 1,50 | 0,5 | 120,0 | 300,0 | Deficiência ácida (limitante) |
| **05** | 0,10 | 1,0 | 4,3 | 10,7 | Proporção estequiométrica 1:1 |
| **06** | 0,50 | 1,0 | 21,4 | 53,5 | Proporção estequiométrica 1:1 |
| **07** | 1,00 | 1,0 | 42,8 | 106,9 | Proporção estequiométrica 1:1 |
| **08** | 1,50 | 1,0 | 64,2 | 160,4 | Proporção estequiométrica 1:1 |
| **09** | 0,10 | 1,5 | 2,9 | 7,1 | Excesso moderado (+50%) |
| **10** | 0,50 | 1,5 | 14,3 | 35,6 | Excesso moderado (+50%) |
| **11** | 1,00 | 1,5 | 28,5 | 71,3 | Excesso moderado (+50%) |
| **12** | 1,50 | 1,5 | 42,8 | 106,9 | Excesso moderado (+50%) |
| **13** | 0,10 | 3,1 | 1,3 | 3,2 | Forte excesso (+210%) |
| **14** | 0,50 | 3,1 | 6,9 | 17,2 | Forte excesso (+210%) |
| **15** | 1,00 | 3,1 | 13,8 | 34,5 | Forte excesso (+210%) |
| **16** | 1,50 | 3,1 | 20,7 | 51,7 | Forte excesso (+210%) |

*Fonte: Adaptado de Bortot Coelho (2017, Apêndice A1.1).*

---

### 4.2.4. Protocolo de Amostragem Temporal com Interrupção Instantânea e Titulação
A coleta de dados cinéticos seguiu o protocolo estrito de amostragem multitemporal com congelamento reacional:
1. Após a estabilização térmica do licor (V = 400 mL a 40,0 °C e 1000 rpm), a massa de calcina m_B0 foi inserida em batelada rápida através de funil de vidro, deflagrando-se o cronômetro no instante de contato sólido-líquido (t = 0);
2. Alíquotas de polpa de 3 mL a 5 mL foram aspiradas por micropipeta graduada dotada de filtro terminal com membrana hidrofílica de acetato de celulose de abertura de poro 0,45 µm nos instantes discretos programados:
   t ∈ {0,5; 1,0; 2,0; 3,0; 4,0; 5,0; 15,0} min
   A retenção física imediata da fase sólida na membrana porosa de 0,45 µm interrompeu instantaneamente o contato reacional no segundo exato da coleta, impedindo a continuidade espúria da dissolução fora do reator;
3. O filtrado límpido de cada amostra foi acidificado com ácido nítrico concentrado a 2% (v/v) para estabilização de cátions solúveis, avolumado e analisado por EAA de chama para determinação das concentrações totais de zinco solúvel (C_Zn,total) e ferro solúvel (C_Fe,total);
4. **Isolamento da Zincita**: Como o ferro em solução advém unicamente da lixiviação residual lenta da ferrita de zinco (ZnFe₂O₄, com razão molar Zn:Fe = 1:2), a concentração líquida de zinco proveniente exclusivamente da zincita solúvel (C_Zn,ZnO) foi isolada por correção estequiométrica:
   C_Zn,ZnO(t) = C_Zn,total(t) - 0,5 · C_Fe,total(t) · (MM_Zn / MM_Fe)
5. A conversão fracionária de zincita X_Zn(t) foi então calculada relacionando a massa de zinco solubilizada de zincita com a massa estequiométrica máxima inicial de zincita contida na carga de calcina:
   X_Zn(t) = [ V · C_Zn,ZnO(t) ] / [ (m_B0 · T_ZnO · MM_Zn) / MM_ZnO ]
6. **Titulação de Acidez Residual**: Ao encerramento da batelada (t = 15,0 min), uma alíquota do filtrado remanescente foi titulada potenciometricamente com solução padronizada de NaOH (0,100 mol/L ou 1,000 mol/L), utilizando-se citrato de sódio como agente quelante mascarante para impedir a precipitação prematura de hidróxidos metálicos de Zn²⁺ e Fe³⁺, quantificando-se com exatidão a concentração de ácido sulfúrico livre final remanescente no licor: C_Af,exp(15 min).

---

## 4.3. Caracterização Granulométrica e Dedução Rigorosa da Distribuição Numérica (RRB ÷ D³)

### 4.3.1. Relevância da Polidispersão Granulométrica no Balanço Populacional
Na lixiviação hidrometalúrgica de concentrados minerais moídos, a taxa global de extração é governada pela área superficial total disponível para o ataque do reagente ácido. Tratar o sólido particulado como um agregado homogêneo de tamanho médio único (abordagem de partícula monodispersa média) introduz severas distorções físicas:
- Subestima acentuadamente a conversão nos primeiros segundos de reação (onde a dissolução ultrarrápida da imensa população de partículas ultrafinas com elevadíssima razão área/volume domina o consumo de ácido);
- Superestima a taxa de retração e a conversão nas etapas tardias (onde o tempo de esgotamento total é controlado exclusivamente pela fração residual dos grãos de maior calibre).

O Balanço Populacional contínuo em batelada (Randolph; Larson, 1988) descreve a evolução da densidade numérica de partículas ψ(D, t) no espaço contínuo de diâmetros D através da Equação Diferencial Parcial hiperbólica de conservação:

```
∂ψ(D, t) / ∂t + ∂[ v(D, t) · ψ(D, t) ] / ∂D = 0
```

com condição inicial no instante de alimentação do reator:

```
ψ(D, 0) = N_T(0) · q_0(D)
```

onde N_T(0) é o número total inicial de partículas sólidas por unidade de volume de suspensão e q_0(D) é a **função densidade de probabilidade de tamanho de partículas em base numérica**.

---

### 4.3.2. Medição Experimental da Distribuição Granulométrica
A determinação experimental do espectro de tamanhos da calcina de zinco (Bortot Coelho, 2017, Tabela 5.4, p. 129) demandou uma metodologia analítica combinada devido à ampla extensão do espectro de partículas:
1. **Peneiramento a Úmido**: Aplicado para a faixa grosseira e intermediária através de série de 8 peneiras de malha quadrada padrão Tyler com aberturas de malha entre 38 µm e 297 µm (malhas 400#, 325#, 270#, 200#, 150#, 100#, 65# e 48#). A lavagem contínua com água desionizada evitou a retenção eletrostática e aglomeração de finos sobre as telas;
2. **Difração de Raios Laser**: Aplicada à fração ultrafina passante na malha Tyler 200# (diâmetro inferior a 74,0 µm) em analisador Helos 12LA da Sympatec GmbH, com dispersor via úmida e desaglomeração prévia por banho ultrassônico de alta frequência.

No ponto de interseção instrumental (abertura de 74,0 µm), ambas as técnicas reportaram concordância de 84,4% de massa acumulada passante, confirmando a continuidade analítica dos dados (Bortot Coelho, 2017).

---

### 4.3.3. Modelo Analítico de Rosin-Rammler-Bennet (RRB) em Base Mássica
A fração mássica acumulada passante F(D) de pós gerados por moagem industrial de minérios é clássica e acuradamente descrita pela função de distribuição de Weibull / Rosin-Rammler-Bennet (Rosin; Rammler, 1933; Bennet, 1936):

```
F(D) = 1 - exp[ - (D / D'_{63,2})^m ]
```

onde:
- D: diâmetro geométrico equivalente da partícula (µm);
- D'_{63,2}: diâmetro característico de escala (µm), no qual 1 - exp(-1) ≈ 63,21% da massa total de partículas possui diâmetro inferior ou igual a D'_{63,2};
- m: módulo de uniformidade ou dispersão granulométrica (adimensional).

A linearização dupla-logarítmica dos pontos experimentais (D_i, F_i) via:

```
ln[ ln( 1 / (1 - F(D)) ) ] = m · ln(D) - m · ln(D'_{63,2})
```

seguida de regressão não-linear por mínimos quadrados (algoritmo de Levenberg-Marquardt com `scipy.optimize.curve_fit`) reproduziu os parâmetros ótimos da literatura de referência:
- D'_{63,2} = 41,65 µm
- m = 1,022

A função densidade de distribuição contínua em base de massa/volume, q_3(D) = dF(D)/dD, é expressa analiticamente por:

```
q_3(D) = (m / D'_{63,2}) · (D / D'_{63,2})^(m - 1) · exp[ - (D / D'_{63,2})^m ]
```

sendo q_3(D) estritamente normalizada no semi-eixo positivo: ∫₀^∞ q_3(D) dD = 1.

---

### 4.3.4. Dedução Matemática da Distribuição Numérica Rigorosa (RRB ÷ D³)
Na literatura prévia de lixiviação de zinco (Bortot Coelho, 2017), a integração do Balanço Populacional vinha sendo realizada assumindo-se direta ou aproximadamente a densidade de distribuição volumétrica/mássica q_3(D) como representativa da população numérica de partículas. 

Essa simplificação conceitual acarreta uma distorção física drástica: como o volume e a massa de uma partícula esférica dependem do cubo do diâmetro (V_p = π · D³ / 6), uma única partícula de 100 µm possui a mesma massa que 1.000.000 de partículas de 1 µm. Consequentemente, utilizar a distribuição em base de massa subestima por ordens de grandeza o número real de partículas finas que povoam a suspensão.

Para restabelecer a consistência termodinâmica e física da modelagem, este trabalho formula a dedução matemática exata da transformação de base mássica para base numérica:

1. Seja dN(D) o número de partículas na suspensão compreendidas no intervalo infinitesimal de diâmetros [D, D + dD], e dM(D) a massa correspondente dessas partículas.
2. Sabendo que dM(D) = M_total · q_3(D) dD e que a massa individual de cada partícula sólida de densidade ρ_sol é dada por m_p(D) = ρ_sol · (π / 6) · D³:

```
dN(D) = dM(D) / m_p(D) = [ M_total · q_3(D) dD ] / [ ρ_sol · (π / 6) · D³ ]
```

3. Agrupando as constantes físicas e a massa total na constante proporcional K_norm = M_total / [ ρ_sol · (π / 6) ], obtém-se:

```
dN(D) = K_norm · [ q_3(D) / D³ ] dD
```

4. A função densidade de probabilidade de tamanho de partícula em base numérica q_0(D), por definição axiomática da teoria de probabilidades, é a distribuição normalizada de dN(D):

```
q_0(D) = dN(D) / ∫₀^∞ dN(u) = [ q_3(D) / D³ ] / ∫₀^∞ [ q_3(u) / u³ ] du
```

Substituindo a expressão analítica do modelo de Rosin-Rammler-Bennet de base mássica q_3(D) na equação acima, obtém-se a **Distribuição Numérica Rosin-Rammler-Bennet Ponderada por Volume Inverso (RRB ÷ D³)**:

```
q_0(D) = [ (m / D'_{63,2}^m) · D^(m - 4) · exp( - (D / D'_{63,2})^m ) ] / I_norm
```

onde a integral de normalização finita é computada analiticamente no domínio regularizado [D_min, D_max] por:

```
I_norm = ∫_{D_min}^{D_max} [ q_3(u) / u³ ] du
```

---

### 4.3.5. Eliminação do Parâmetro Empírico de Retardo (α = 0)
A consequência físico-matemática mais marcante da dedução da distribuição numérica RRB ÷ D³ reside na **completa eliminação da necessidade do parâmetro cinético empírico de amortecimento α**.

Nos estudos mecanicistas anteriores (Bortot Coelho, 2017), a taxa de retração interfacial linear do White-Box necessitava de um parâmetro arbitrário de retardamento (α_nominal = 5.500 µm/min) subtraído da força motriz de dissolução:
v(t) = - (2 / ρ_s) · [ k_s · C_Af(t) - α · (C_A0 - C_Af(t)) ]

Esse parâmetro α havia sido introduzido de forma puramente empírica com o propósito de frear o modelo mecanicista nos instantes intermediários, pois o modelo com a distribuição q_3(D) apresentava uma curvatura de consumo de ácido incompatível com a bancada.

Com a introdução da base numérica correta q_0(D) ∝ q_3(D) / D³, o modelo populacional passa a capturar de modo exato a enorme contribuição de área superficial e a quase instantânea extinção dos ultrafinos nos primeiros 30 segundos, seguida pela desaceleração natural da retração controlada pelos grãos maiores. Desse modo, o parâmetro empírico α deixa de ter qualquer justificativa física e é formalmente eliminado no modelo mecanicista White-Box de referência:

```
α = 0 µm/min
```

o que restaura a lei cinética pura de retração intrínseca do Núcleo em Diminuição (SCM de Balarini, 2009 e Levenspiel, 1999).

---

## 4.4. Formulação Fenomenológica: Cinética Interfacial (SCM) e Balanço de Herbst

### 4.4.1. Mecanismo Cinético Heterogêneo: Modelo do Núcleo em Diminuição (SCM)
A reação química de dissolução da calcina em meio aquoso ácido sulfúrico é representada pela estequiometria fundamental:

```
ZnO (s) + H₂SO₄ (aq) ──► ZnSO₄ (aq) + H₂O (l)
```

Para partículas sólidas densas sem formação de camada passivante espessa insolúvel sob regime turbulento de agitação mecânica (1000 rpm), o avanço reacional é regido pelo Modelo do Núcleo em Diminuição (*Shrinking Core Model* — SCM) ou Modelo da Partícula Reagente de Tamanho Decrescente (*Shrinking Particle Model*), sob estrito controle por reação química superficial (Levenspiel, 1999; Szekely; Evans; Sohn, 1976; Balarini, 2009).

O balanço molar diferencial na interface sólida de uma partícula esférica de diâmetro D é expresso por:

```
- dn_B / dt = - d/dt [ ρ_s · (π · D³ / 6) ] = - (ρ_s · π · D² / 2) · (dD / dt) = π · D² · r_s
```

onde r_s é a taxa de reação química por unidade de área superficial (mol · µm⁻² · min⁻¹).

Assumindo cinética de primeira ordem em relação à concentração de ácido sulfúrico livre remanescente no seio da solução C_Af(t) (Levenspiel, 1999; Balarini, 2009), tem-se r_s = k_s · C_Af(t). Isolando a derivada temporal do diâmetro da partícula (dD/dt), obtém-se a velocidade linear intrínseca de retração diametral interfacial:

```
v(t) = dD / dt = - (2 / ρ_s) · k_s · C_Af(t)
```

onde:
- v(t): velocidade linear instantânea de retração diametral (µm/min);
- k_s: constante cinética intrínseca de reação química superficial (k_s = 1,8 × 10⁴ µm/min a 40 °C, determinada por Balarini, 2009, p. 115);
- ρ_s: densidade molar da zincita sólida pura (69,2 mol/L);
- C_Af(t): concentração instantânea de ácido sulfúrico livre remanescente no licor aquoso (mol/L).

Note-se que v(t) independe do diâmetro instantâneo D da partícula: todas as classes granulométricas presentes na polpa sofrem retração linear na mesma velocidade pontual v(t) em um dado instante t.

---

### 4.4.2. Balanço Estequiométrico de Conservação de Massa em Batelada (Herbst, 1979)
Em um reator operado em batelada com volume líquido aproximadamente constante V, o consumo de ácido sulfúrico na fase aquosa está estritamente acoplado à dissolução mássica acumulada de óxido de zinco pela estequiometria 1:1 da reação.

A relação exata de conservação de massa que relaciona a concentração de ácido livre instantânea C_Af(t) à conversão fracionária global de zinco X_Zn(t) foi deduzida por Herbst (1979) e é formalizada por:

```
C_Af(t) = C_A0 · [ 1 - X_Zn(t) / η ]
```

onde:
- C_A0: concentração inicial de ácido sulfúrico adicionada na alimentação (mol/L);
- η: razão molar estequiométrica inicial de alimentação (adimensional);
- X_Zn(t): conversão fracionária global acumulada de zincita (0 ≤ X_Zn(t) ≤ 1).

A Equação de Herbst impõe os limites termodinâmicos rigorosos do sistema:
1. **Regime com Ácido em Excesso (η > 1,0)**: Quando a conversão de zincita atinge a totalidade (X_Zn = 1,0), a concentração residual final de ácido livre estabiliza-se no patamar positivo assintótico:
   C_Af,final = C_A0 · [ 1 - 1 / η ] > 0
2. **Regime com Ácido Estequiométrico (η = 1,0)**: No esgotamento simultâneo de sólidos e ácido (X_Zn = 1,0), a acidez anula-se exatamente: C_Af,final = 0 mol/L;
3. **Regime com Ácido Deficitário Limitante (η < 1,0)**: O consumo de ácido é exaurido (C_Af = 0 mol/L) quando a conversão de zinco atinge o teto estequiométrico máximo teórico:
   X_Zn^Max = η < 1,0
   A partir desse instante, a dissolução cessa irreversivelmente por ausência física de solvente reagente.

---

### 4.4.3. Projeção Física de Irreversibilidade e Não-Crescimento
Como a reação de lixiviação ácida de óxido de zinco a 40 °C é termodinamicamente irreversível (variação de energia livre de Gibbs padrão amplamente negativa, ΔG°_298K ≈ -94 kJ/mol), as partículas sólidas em suspensão não podem sofrer precipitação espontânea ou crescimento de diâmetro caso a concentração de ácido se anule. 

Para impedir violações físicas em algoritmos de integração numérica, a taxa de retração interfacial é submetida a um operador de projeção física unilateral rígida:

```
v(t) = min( 0, dD/dt )
```

assegurando que |v(t)| = - v(t) ≥ 0 para todo instante t.

---

## 4.5. Resolvedor Numérico do Balanço Populacional em Batelada (BatchPBMSolver)

### 4.5.1. Resolução pelo Método das Características e Deslocamento Diametral δ(t)
A integração temporal da Equação Diferencial Parcial do Balanço Populacional:

```
∂ψ(D, t) / ∂t + v(t) · [ ∂ψ(D, t) / ∂D ] = 0
```

com a propriedade de que v(t) é espacialmente uniforme no domínio de diâmetros, é resolvida com exatidão pelo Método das Características (Randolph; Larson, 1988; Balarini, 2009).

As curvas características no plano espaço-tempo (D × t) satisfazem a Equação Diferencial Ordinária:

```
dD / dt = v(t) = - |v(t)|
```

cuja integração direta a partir de um diâmetro inicial D_0 no instante t = 0 resulta em:

```
D(t) = D_0 - ∫₀ᵗ |v(τ)| dτ = D_0 - δ(t)
```

onde define-se o **operador de deslocamento diametral acumulado** δ(t):

```
δ(t) = ∫₀ᵗ |v(τ)| dτ ≥ 0  (µm)
```

com condição física inicial óbvia δ(0) = 0. 

A grandeza escalar δ(t) quantifica a espessura total em micrômetros de camada sólida que foi quimicamente removida da superfície de todas as partículas da polpa desde o início da reação até o instante t.

Pelo princípio da conservação populacional ao longo das características, a densidade de distribuição de diâmetros no instante t relaciona-se à distribuição inicial por uma translação rígida para a esquerda no eixo de tamanhos:

```
ψ(D, t) = ψ(D + δ(t), 0)   para D > 0
```

partículas cujo diâmetro inicial satisfazia D_0 ≤ δ(t) já foram integralmente solubilizadas e desapareceram da fase sólida.

---

### 4.5.2. Cálculo da Conversão Fracionária via Momento de Terceira Ordem M_3(t)
A massa total de sólidos retidos na suspensão no instante t é diretamente proporcional ao momento estatístico de terceira ordem da distribuição populacional, M_3(t), definido por:

```
M_3(t) = ∫₀^∞ D³ · ψ(D, t) dD = N_T(0) · ∫_{δ(t)}^∞ (D₀ - δ(t))³ · q_0(D₀) dD₀
```

A conversão fracionária global de zincita X_Zn(t) representa a fração de massa que foi transferida para a fase aquosa, sendo computada analiticamente pela razão entre os momentos de terceira ordem:

```
X_Zn(t) = 1 - [ M_3(t) / M_3(0) ]
```

onde:

```
M_3(0) = ∫₀^∞ D₀³ · q_0(D₀) dD₀
```

e

```
M_3(t) = ∫_{δ(t)}^{D_max} [ D₀ - δ(t) ]³ · q_0(D₀) dD₀
```

com a condição de saturação física de que se δ(t) ≥ D_max, então M_3(t) = 0 e X_Zn(t) = 1,0.

---

### 4.5.3. Condição de Contorno Hardcoded em t = 0 e Exclusão Estrita nos Modelos
Uma das formulações metodológicas centrais implementadas e consolidadas neste trabalho consiste no **tratamento rigoroso da condição inicial no tempo zero (t = 0)**.

Por estrita definição termodinâmica e cinemática do início da batelada, no instante em que o sólido particulado toca a solução aquosa:
- Nenhuma massa de zinco teve tempo infinitesimal para reagir e solubilizar: **X_Zn(0) = 0,00000**;
- Nenhuma espessura de camada sólida foi removida das partículas: **δ(0) = 0,00000 µm**;
- A concentração de ácido livre na fase líquida é exatamente a concentração inicial alimentada: **C_Af(0) = C_A0 mol/L**.

Nas tentativas preliminares de modelagem híbrida da literatura, costumava-se incluir o par (t = 0, X_Zn = 0) diretamente nas tabelas de treinamento supervisionado dos modelos de aprendizado de máquina e nos resolvedores de regressão. 

Essa prática induzia severas patologias numéricas e conceituais:
1. No intervalo ultrarrápido inicial entre t = 0 e t = 0,5 min, a taxa de retração interfacial instantânea |v(t)| atinge valores elevadíssimos (|v_0| > 150 µm/min), enquanto a conversão acumulada X_Zn ainda salta de 0 para valores entre 0,40 e 0,75. Forçar um regressor Black-Box estatístico a aprender simultaneamente o ponto nulo (t = 0) e a magnitude colossal da derivada impunha gradientes numéricos explosivos e instabilidades de perda de monotonicidade;
2. Como X_Zn(0) = 0 é uma condição de contorno determinística mandatória da física, é conceitualmente redundante e danoso gastar capacidade de parametrização da inteligência artificial para aproximar numericamente um valor que é rigorosamente conhecido a priori.

Diante dessas constatações, estabeleceu-se a seguinte diretriz metodológica definitiva:
1. **Condição Inicial Hardcoded**: A condição física inicial no tempo t = 0 é fixada deterministicamente de forma rígida (*hardcoded*) no código-fonte do resolvedor híbrido:
   X_Zn(0) ≡ 0,0
   δ(0) ≡ 0,0
   C_Af(0) ≡ C_A0
2. **Exclusão Estrita de t = 0 do Aprendizado e Métricas**: Todos os pares de dados associados ao tempo t = 0 foram estritamente eliminados dos conjuntos de dados de treinamento, validação cruzada, teste cego e cálculo de métricas de erro dos modelos de aprendizado de máquina (DDM).
3. **Domínio Temporal Ativo**: O regressor opera e é avaliado estritamente sobre a malha temporal positiva:
   t > 0  (com t ∈ [0,25; 15,00] min para malhas densas e t ∈ {0,5; 1,0; 2,0; 3,0; 4,0; 5,0; 15,0} min para os ensaios de bancada).

Essa modificação purificou o espaço de treinamento estatístico, permitindo que as redes neurais e regressores foquem com máxima precisão no decaimento cinético contínuo e na cauda assintótica das reações.

---

## 4.6. Formulação do Problema Inverso e Geração dos Alvos Cinéticos |v(t)|

### 4.6.1. A Problemática Inversa da Não-Observabilidade de |v(t)|
Em suspensões heterogêneas polidispersas industriais ou de laboratório sob agitação violenta (1000 rpm), é fisicamente inviável medir a derivada temporal pontual do encolhimento de uma partícula micrométrica individual (|v(t)| = |dD/dt|) em tempo real. As variáveis macroscópicas passíveis de medição experimental nos 16 ensaios de bancada restringem-se à conversão global de zincita X_Zn,exp(t_i) nos 7 instantes de amostragem ativa pós-alimentação:
t_i ∈ {0,5; 1,0; 2,0; 3,0; 4,0; 5,0; 15,0} min (perfazendo N = 16 ensaios × 7 pontos = 112 pontos ativos).

Para treinar supervisionadamente os modelos de aprendizado de máquina DDM capazes de prever a taxa constitutiva |v(t)| em função das condições operacionais, foi indispensável conceber e resolver um **Problema Inverso de Otimização Dinâmica Regularizada** (Tarantola, 2005; Aster; Borchers; Thurber, 2018): identificar qual perfil temporal contínuo |v(t)|, quando convoluído com a distribuição numérica RRB ÷ D³ no resolvedor mecanicista `BatchPBMSolver`, reproduz com máxima fidelidade os perfis experimentais de conversão observados em cada ensaio.

---

### 4.6.2. Parametrização Bi-Exponencial Regularizada
A taxa de retração interfacial de pós minerais exibe dinâmicas multiescalares com dois regimes temporais predominantes:
1. Um regime cinético primário ultrarrápido (t < 1,0 min), associado à acidez máxima e ataque à alta rugosidade superficial dos grãos;
2. Um regime secundário atenuado e suave (t ≥ 1,0 min), onde o consumo de acidez e a diminuição da área interfacial promovem desaceleração monotônica.

Para mapear de forma contínua, analítica e suave essa dinâmica sem introduzir oscilações numéricas ou descontinuidades, a trajetória temporal |v(t)| de cada ensaio foi modelada por uma função bi-exponencial estritamente não-negativa parametrizada pelo vetor de coeficientes θ = [a₁, b₁, a₂, b₂, c]^T:

```
|v(t; θ)| = a₁ · exp( - b₁ · t ) + a₂ · exp( - b₂ · t ) + c
```

com coeficientes restritos ao semi-eixo positivo (a₁, b₁, a₂, b₂, c ≥ 0), onde:
- a₁: amplitude do pulso cinético primário ultrarrápido (µm/min);
- b₁: constante de decaimento de primeira ordem da reação primária (min⁻¹);
- a₂: amplitude da componente de dissolução secundária intermediária (µm/min);
- b₂: constante de decaimento de primeira ordem da reação secundária (min⁻¹);
- c: velocidade residual assintótica em tempos longos (µm/min).

---

### 4.6.3. Solução Analítica Exata da Retração Diametral Integrada δ(t; θ)
A escolha metodológica da parametrização bi-exponencial confere uma vantagem matemática decisiva: a integral temporal do encolhimento diametral possui **solução analítica fechada exata**:

```
δ(t; θ) = ∫₀ᵗ |v(τ; θ)| dτ = (a₁ / b₁) · [ 1 - exp( - b₁ · t ) ] + (a₂ / b₂) · [ 1 - exp( - b₂ · t ) ] + c · t
```

satisfazendo rigorosamente a condição inicial física δ(0; θ) ≡ 0.

A existência de solução analítica fechada para δ(t; θ) elimina a necessidade de integração numérica passo-a-passo de equações diferenciais durante a otimização inversa, acelerando a convergência do algoritmo em ordens de grandeza e garantindo que dδ/dt = |v(t)| ≥ 0 para qualquer instante temporal.

---

### 4.6.4. Função-Objetivo e Algoritmo Quase-Newton L-BFGS-B Multi-Start
A estimação dos parâmetros ótimos θ* para cada ensaio k (k = 1, ..., 16) foi formulada pela minimização da função-objetivo de resíduos ponderados quadráticos acrescida de penalização de barreira assintótica:

```
min_θ J(θ) = ∑_{i=1}^{N_pontos} [ X_pred(t_i; θ) - X_exp(t_i) ]² + λ_tail · [ |v(15; θ)| ]²
```

onde:
- X_pred(t_i; θ) = 1 - [ M_3(δ(t_i; θ)) / M_3(0) ];
- N_pontos = 7 (pontos experimentais ativos em t > 0);
- λ_tail = 10⁻⁴ (fator de regularização que assegura decaimento suave da velocidade residual no encerramento da batelada a t = 15 min).

A otimização foi executada via algoritmo quase-Newton L-BFGS-B (*Limited-memory Broyden-Fletcher-Goldfarb-Shanno with Boundary constraints*), implementado na biblioteca `scipy.optimize.minimize` com limites de busca estritos baseados na termodinâmica do sistema e estratégia de múltiplos pontos de partida (*multi-start* com 5 estimativas iniciais distintas) para blindar a rotina contra aprisionamento em mínimos locais.

A otimização inversa convergiu perfeitamente nos 16 ensaios de bancada, alcançando índice de determinação global R² = 0,99896 (com R² > 0,990 em todos os 16 ensaios individualmente, RMSE global de 0,0098 e MAE global de 0,0071), validando a exatidão da reconstrução mecanicista.

---

### 4.6.5. Redução de Dimensionalidade (3 Variáveis Ativas) e Bases Geradas
A partir dos parâmetros ótimos θ* obtidos, consolidaram-se as bases de dados supervisionadas para o treinamento dos regressores DDM. 

Nesta etapa, implementou-se uma decisão fundamental de **Engenharia de Atributos**:
- Nos modelos preliminares anteriores, utilizavam-se 4 variáveis de entrada: [temperatura_C, C_A0, η, t];
- Como os 16 ensaios de bancada de Bortot Coelho (2017) foram executados sob rigoroso controle isotérmico em temperatura constante de 40,0 °C, a inclusão da coluna de temperatura configurava uma redundância estática (variância zero) que provocava multicolinearidade espúria e degeneração de posto nas matrizes de covariância dos regressores.

Conduziu-se a redução de dimensionalidade estrita para **3 variáveis cinéticas ativas (input_dim = 3)**:

```
X = [ C_A0, η, t ]
```

sendo os dados consolidados em:
1. **Base de Alvos Experimentais Ativos (`alvos_v_treinamento.csv`)**: 112 amostras ativas (16 ensaios × 7 tempos em t > 0);
2. **Base de Alvos em Malha Fina Regular (`alvos_v_treinamento_denso.csv`)**: 960 amostras ativas distribuídas uniformemente com passo fino de Δt = 0,25 min no intervalo t ∈ [0,25; 15,00] min (16 ensaios × 60 passos temporais por ensaio), essencial para garantir continuidade e suporte numérico denso para o treinamento das redes neurais profundas.

---

## 4.7. Modelagem Orientada por Dados (Black-Box): Formulação, Regularização e o Protagonismo do MLP

### 4.7.1. Formulação dos Quatro Algoritmos Concorrentes
Para estimar a lei de retração interfacial |v(t)| = f(C_A0, η, t), quatro famílias distintas de algoritmos de aprendizado de máquina supervisionado foram calibradas e submetidas a benchmark:

#### 1. Multi-Layer Perceptron (MLP em PyTorch — Arquitetura Protagonista)
O MLP mapeia o vetor de entrada tridimensional normalizado x_norm = [C_A0,norm, η_norm, t_norm]^T através de camadas densas lineares intercaladas com funções de ativação analíticas não-lineares suaves. A propagação direta na l-ésima camada oculta é dada por:

```
h^(l) = GELU( LayerNorm( W^(l) · h^(l-1) + b^(l) ) )
```

onde:
- W^(l) e b^(l) representam a matriz de pesos sinápticos e o vetor de bias;
- LayerNorm representa a normalização por camada, que estabiliza o fluxo de gradientes e acelera a convergência;
- GELU (*Gaussian Error Linear Unit*, Hendrycks; Gimpel, 2016) é a função de ativação suave definida por:
  GELU(u) = u · Φ(u) = u · P(U ≤ u), com U ~ N(0, 1)

A função GELU possui a propriedade crítica de ser **infinitamente diferenciável (pertencente à classe C∞)**, ao contrário da função ReLU tradicional que possui descontinuidade de primeira derivada em zero. Essa característica C∞ assegura que a superfície predita de velocidades seja suave e continuamente integrável por métodos numéricos de equações diferenciais ordinárias.

Para assegurar estritamente a não-negatividade física (|v(t)| ≥ 0) e a estabilização da faixa dinâmica que varia por quatro ordens de grandeza (de 0,01 µm/min a mais de 100 µm/min), o MLP foi treinado prevendo o logaritmo deslocado da velocidade z = ln(1 + |v|), com a predição na escala original obtida pela transformação inversa exata:

```
|v_pred| = exp( z_pred ) - 1
```

O treinamento foi otimizado via algoritmo AdamW (Loshchilov; Hutter, 2019) com taxa de aprendizado inicial α_lr = 10⁻³, escalonamento por decaimento de cosseno (*CosineAnnealingLR*), penalização L_2 nos pesos (*weight decay* λ_w = 10⁻⁴) e parada antecipada (*Early Stopping*) com paciência de 30 épocas guiada pela perda da dobra de validação.

#### 2. Random Forest Regressor (RF Regularizado)
O regressor *Random Forest* (Breiman, 2001) é um comitê baseado na agregação *Bootstrap* (*Bagging*) de B = 100 árvores de decisão descorrelacionadas. Cada árvore é ajustada sobre subamostragens com reposição do conjunto de dados de treino. Para evitar sobreajuste aos pontos extremos, foram impostas restrições de profundidade máxima (max_depth = 6) e tamanho mínimo de folha (min_samples_leaf = 2), operando sobre o alvo transformado z = ln(1 + |v|).

#### 3. Support Vector Regression (SVR com Kernel RBF)
A regressão por vetores de suporte (Smola; Schölkopf, 2004) busca uma função em espaço de Hilbert de dimensão infinita que contenha os resíduos dentro de um tubo ε-insensível, penalizando desvios lineares externos via parâmetro de custo C = 10,0, tolerância ε = 0,05 e núcleo de Função de Base Radial Gaussiana (RBF):

```
K(x_i, x_j) = exp( - γ · ||x_i - x_j||² )
```

#### 4. Extreme Gradient Boosting (XGBoost Regressor)
O algoritmo XGBoost (Chen; Guestrin, 2016) constrói árvores de decisão aditivas sequenciais de forma gulosa, minimizando a expansão de Taylor de segunda ordem da função de perda com regularização L_2 sobre os pesos das folhas (learning_rate = 0,05, max_depth = 4, subsample = 0,80, 150 estimadores).

---

### 4.7.2. Protocolo de Partição de Dados: Validação Cruzada Disjunta e Teste Cego
Para garantir uma avaliação estatística e prevenir vazamento de dados (*data leakage*), adotou-se o seguinte protocolo rigoroso de particionamento:
1. **Conjunto de Teste Cego Independente (Out-of-Sample)**: Dos 16 ensaios da matriz fatorial, 3 ensaios representativos dos três regimes operacionais foram integralmente retirados e mantidos intocados durante todas as fases de calibração, ajuste de hiperparâmetros e treinamento:
   - **Ensaio 08**: Proporção estequiométrica neutra (C_A0 = 1,50 mol/L, η = 1,0);
   - **Ensaio 14**: Leve excesso de ácido (C_A0 = 0,50 mol/L, η = 1,5);
   - **Ensaio 07**: Forte excesso de ácido (C_A0 = 1,00 mol/L, η = 3,1).
   Esses 3 ensaios perfazem 21 pontos experimentais em t > 0 e 180 pontos densos;
2. **Conjunto de Treinamento e Validação Cruzada (13 Ensaios)**: Os 13 ensaios restantes (91 pontos experimentais ativos e 780 pontos densos em t > 0) foram estruturados em uma validação cruzada espacial estratificada por grupos (`GroupKFold` com K = 4 dobras disjuntas agrupadas por ensaio completo). Nenhuma amostra de um mesmo ensaio foi simultaneamente compartilhada entre treino e validação, garantindo que as métricas de validação meçam a real capacidade de interpolação entre condições operacionais.

---

### 4.7.3. Otimização Arquitetural do MLP e Destilação de 4-Fold Deep Ensemble
Na concepção do modelo neural protagonizado, exploraram-se quatro topologias arquiteturais distintas em PyTorch (conforme detalhado na Tabela 4.2):
- **MLP-A (Compacta GELU)**: Duas camadas ocultas densas [32, 16], ativação GELU, sem conexões residuais;
- **MLP-B (Padrão GELU — Topologia Campeã)**: Duas camadas ocultas balanceadas [64, 32], ativação GELU, LayerNorm, sem resíduo;
- **MLP-C (Profunda SiLU)**: Três camadas densas [128, 64, 32], função de ativação SiLU / Swish [u · σ(u)];
- **ResNet-MLP (Residual GELU)**: Arquitetura com blocos de salto residual (*skip-connections*) ligando a entrada diretamente às camadas intermediárias [64, 32].

**Tabela 4.2 – Desempenho comparativo das arquiteturas de MLP na validação cruzada (4 dobras disjuntas, t > 0).**

| Arquitetura | Topologia | Ativação | Conexão Residual | R² Médio (CV) | R²_log Médio | RMSE Médio (µm/min) | MAE Médio (µm/min) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MLP-B (Padrão GELU)** | `[64, 32]` | GELU | Não | **0,8210 ± 0,1092** | **0,7696** | **3,25** | **1,06** |
| **MLP-A (Compacta GELU)** | `[32, 16]` | GELU | Não | 0,8233 ± 0,0790 | 0,7298 | 3,47 | 1,08 |
| **MLP-C (Profunda SiLU)** | `[128, 64, 32]` | SiLU | Não | 0,6800 ± 0,2166 | 0,7737 | 4,37 | 1,32 |
| **ResNet-MLP (Residual)** | `[64, 32]` | GELU | Sim | 0,3849 ± 0,4720 | 0,7396 | 6,39 | 2,12 |

A topologia **MLP-B** destacou-se pela estabilidade e superioridade em escala logarítmica (R²_log = 0,7696) com menor dispersão de resíduos.

Para maximizar a robustez preditiva e mitigar a variância estocástica da inicialização de pesos, os 4 modelos treinados durante as 4 dobras da validação cruzada foram consolidados através de uma **Destilação de Deep Ensemble (4-Fold Ensemble)**. 

A predição final do MLP Ensemble e a sua incerteza epistêmica associada são expressas pela média e desvio padrão das 4 sub-redes:

```
z_pred(x) = (1 / 4) · ∑_{k=1}^4 z_k(x)
σ_z(x) = √[ (1 / 3) · ∑_{k=1}^4 ( z_k(x) - z_pred(x) )² ]
```

---

### 4.7.4. Extração Analítica de Sensibilidades Físicas via `torch.autograd`
Em virtude da formulação contínua e da classe de diferenciabilidade C∞ da ativação GELU, o modelo neural MLP-B em PyTorch permite o cálculo exato e instantâneo das derivadas parciais analíticas da velocidade de retração em relação a qualquer variável de processo via motor de diferenciação automática (`torch.autograd`), dispensando aproximações imprecisas por diferenças finitas:

```
Sensibilidade ao Ácido:        S_{C_A0}(t) = ∂|v| / ∂C_A0
Sensibilidade à Razão Molar:   S_η(t)      = ∂|v| / ∂η
Sensibilidade Temporal:        S_t(t)      = ∂|v| / ∂t
```

A extração das sensibilidades analíticas comprovou a coerência físico-química da rede:
- ∂|v|/∂C_A0 > 0 para todo t, confirmando que o aumento da concentração inicial de ácido intensifica monotônicamente a taxa de ataque à superfície mineral;
- ∂|v|/∂t < 0 para todo t, refletindo o amortecimento suave imposto pelo consumo contínuo de solvente e arredondamento dos sítios ativos das partículas;
- ∂|v|/∂η > 0 nos regimes de deficiência ácida, estabilizando-se em platô assintótico para η > 1,5, indicando que a partir de moderado excesso de ácido o processo satura o controle superficial.

---

## 4.8. Seleção Multicritério do Modelo Campeão (MCDA - Opção 5)

### 4.8.1. Fundamentação da Decisão Multicritério para Modelagem Híbrida
A escolha do algoritmo caixa-preta que deve alimentar um modelo mecanicista de engenharia química (PBM) não pode se basear exclusivamente no coeficiente de determinação estático linear R² no teste cego. 

Em sistemas acoplados a equações diferenciais, critérios como a suavidade analítica, a precisão nas baixas velocidades da cauda assintótica e a fidelidade da integral temporal são determinantes:
1. **Modelos em Árvore (Random Forest e XGBoost)**: Embora atinjam coeficientes R² elevados na escala linear grosseira, são funções constantes por partes (classe C⁰ com derivada temporal identicamente nula em quase todo o domínio e descontinuidades infinitas nos pontos de partição nodal). Quando inseridos dentro de resolvedores de equações diferenciais ordinárias (ODEs) ou algoritmos de controle preditivo baseados em gradientes, geram ruídos e instabilidades;
2. **Importância da Cauda Assintótica (R²_log)**: Os instantes finais de lixiviação envolvem velocidades residuais muito baixas (|v| < 1,0 µm/min). Um modelo que apresente erro absoluto de 0,5 µm/min nesses tempos acumula desvios percentuais gigantescos que inviabilizam a previsão do tempo de residência necessário para o esgotamento do reator;
3. **Fidelidade da Retração Integrada δ(t)**: O Balanço Populacional não responde instantaneamente a variações ruidosas pontuais de |v(t)|, mas sim à integral acumulada δ(t) = ∫₀ᵗ |v(τ)| dτ. Logo, o coeficiente de determinação da retração integrada (R²_δ) reflete com muito maior fidelidade o acoplamento real com o PBM.

---

### 4.8.2. Formulação e Pesos da Matriz de Decisão Multicritério (Opção 5)
Para selecionar imparcialmente o modelo campeão, estabeleceu-se a **Matriz de Decisão Multicritério Aprofundada (MCDA - Opção 5)**, fundamentada em 5 critérios analíticos normalizados no intervalo [0, 100], com seus respectivos pesos percentuais:

1. **Critério 1: Generalização Cega em Escala Linear R² (Peso = 20%)**: Mede a capacidade preditiva macroscópica sobre os 3 ensaios de teste cego intocados;
2. **Critério 2: Acurácia Multiescala na Cauda Assintótica R²_log (Peso = 25%)**: Avalia a qualidade do ajuste no espaço transformado ln(1 + |v|), penalizando severamente desvios percentuais em baixas velocidades na cauda da batelada;
3. **Critério 3: Fidelidade na Retração Diametral Integrada R²_δ (Peso = 20%)**: Mede o coeficiente de determinação entre a integral cumulativa predita δ_pred(t) e a integral de referência δ_exp(t) no teste cego;
4. **Critério 4: Classe de Diferenciabilidade Analítica C∞ e Autograd (Peso = 25%)**: Pontua a adequação matemática ao acoplamento com o PBM mecanicista (100 pontos para C∞ contínuo com suporte nativo a diferenciação automática `Autograd`; 70 pontos para C∞ sem autograd nativo; e 10 pontos para funções em degrau descontínuas C⁰ de árvores de decisão);
5. **Critério 5: Latência Computacional em Inferência Vetorizada em Lote (Peso = 10%)**: Mede a velocidade de cálculo por 1000 avaliações de pontos de malha (essencial para simulações de dinâmicas em tempo real e otimização de plantas industriais).

A pontuação global de cada modelo i é dada pela soma ponderada:

```
Score_MCDA(i) = ∑_{j=1}^5 w_j · Nota_normalizada(i, j)
```

A Tabela 4.3 consolida as métricas empíricas e o veredito final da Matriz MCDA.

**Tabela 4.3 – Matriz de Análise de Decisão Multicritério (MCDA - Opção 5) para seleção do modelo Black-Box campeão (t > 0, 3 Variáveis de Entrada).**

| Critério Analítico | Peso (%) | MLP (PyTorch C∞) | Random Forest | SVR (RBF) | XGBoost | Unidade / Critério |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **1. R² Teste Cego (Escala Linear)** | 20% | 0,9231 (92,3) | **0,9539 (95,4)** | 0,9041 (90,4) | 0,8117 (81,2) | Maior é melhor |
| **2. R²_log Cauda Assintótica** | 25% | **0,9453 (94,5)** | 0,8158 (81,6) | 0,9078 (90,8) | 0,7771 (77,7) | Maior é melhor |
| **3. R²_δ Retração Integrada ∫\|v\|dt** | 20% | 0,9490 (94,9) | 0,8512 (85,1) | **0,9651 (96,5)** | 0,8821 (88,2) | Maior é melhor |
| **4. Diferenciabilidade C∞ e Autograd** | 25% | **C∞ + Autograd (100,0)** | C⁰ Degraus (10,0) | C∞ Sem Autograd (70,0) | C⁰ Degraus (10,0) | Suavidade em EDOs |
| **5. Velocidade de Inferência (Lote)** | 10% | **0,19 ms (95,0)** | 30,37 ms (30,0) | 3,97 ms (75,0) | 0,28 ms (90,0) | 1000 avaliações |
| **Violação Física (\|v\| < 0)** | Restrição | **0,00%** | **0,00%** | **0,00%** | **0,00%** | Inegociável (0,00%) |
| **PONTUAÇÃO FINAL MCDA (0-100)** | **100%** | **92,84** | **64,50** | **79,91** | **54,14** | **Classificação** |
| **Veredito Formal** | — | **CAMPEÃO ABSOLUTO** | Vice-Campeão | 3º Lugar | 4º Lugar | — |

O **Multi-Layer Perceptron (MLP)** consagrou-se como o **Modelo Campeão da Modelagem Híbrida com Score MCDA de 92,84/100**, superando amplamente o SVR (79,91), o Random Forest (64,50) e o XGBoost (54,14).

---

## 4.9. Concepção e Acoplamento da Arquitetura Híbrida Serial (DDM → PBM)

### 4.9.1. Fluxo de Informação e Algoritmo de Execução Serial
Na arquitetura híbrida serial concebida (*Grey-Box Serial: DDM → PBM*), a rede neural MLP atua na vanguarda cinética, enquanto as equações mecanicistas populacionais e estequiométricas impõem a física fundamental e os limites termodinâmicos de conservação (Figura 4.2).

O algoritmo computacional de simulação híbrida executa a seguinte sequência de passos em cada intervalo de tempo:

1. **Condição Inicial (t = 0)**: 
   Fixa-se deterministicamente:
   X_Zn(0) = 0,0
   δ(0) = 0,0 µm
   C_Af(0) = C_A0 mol/L

2. **Propagação Temporal Discretizada (para t_k = Δt, 2Δt, ..., t_final)**:
   a) O vetor de atributos operacionais x_k = [C_A0, η, t_k] é normalizado e injetado no modelo neural MLP Campeão;
   b) A rede infere o escalar logarítmico z_k e computa a velocidade linear instantânea de retração:
      |v_pred(t_k)| = max( 0, exp(z_pred(x_k)) - 1 )  (µm/min)
   c) A retração diametral acumulada δ(t_k) é atualizada pela integração trapezoidal cumulativa positiva:
      δ(t_k) = δ(t_{k-1}) + 0,5 · [ |v_pred(t_{k-1})| + |v_pred(t_k)| ] · (t_k - t_{k-1})
   d) O valor de δ(t_k) é transmitido ao resolvedor mecanicista `BatchPBMSolver`, que convolui o encolhimento diametral com a distribuição numérica inicial Rosin-Rammler-Bennet ponderada por volume (RRB ÷ D³):
      M_3(t_k) = ∫_{δ(t_k)}^{D_max} [ D₀ - δ(t_k) ]³ · q_0(D₀) dD₀
   e) A conversão mássica acumulada de zincita no instante t_k é obtida pela razão dos momentos volumétricos:
      X_Zn,hibrido(t_k) = 1 - [ M_3(t_k) / M_3(0) ]
   f) Aplica-se a projeção física de monotonicidade temporal e teto estequiométrico:
      X_Zn,hibrido(t_k) = min( min( 1,0; η ), max( X_Zn,hibrido(t_{k-1}), X_Zn,hibrido(t_k) ) )
   g) A concentração residual de ácido livre no licor aquoso C_Af(t_k) é atualizada algebricamente pela relação estequiométrica de conservação de Herbst (1979):
      C_Af(t_k) = C_A0 · [ 1 - X_Zn,hibrido(t_k) / η ]
   h) Se C_Af(t_k) ≤ 0, a força motriz química é exaurida e o algoritmo congela a conversão para os passos subsequentes.

```
       [ Variáveis Operacionais: C_A0, η, t ]
                         │
                         ▼
             ┌───────────────────────┐
             │   MLP Campeão (C∞)    │ ──► Predição de |v(t)| (µm/min)
             └───────────────────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │  Quadratura Numérica  │ ──► Cálculo de δ(t) = ∫|v|dt (µm)
             └───────────────────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │  PBM (RRB ÷ D³)       │ ──► Convolução Populacional M_3(t)
             └───────────────────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │  Balanço de Herbst    │ ──► Atualização de C_Af(t) e X_Zn(t)
             └───────────────────────┘
                         │
                         ▼
             [ Saídas: X_Zn(t), C_Af(t), ψ(D, t) ]
```
*Figura 4.2 – Diagrama de blocos do acoplamento híbrido serial DDM → PBM.*

---

### 4.9.2. Protocolo de Benchmark Triplo e Métricas Estatísticas
Para demonstrar quantitativamente o ganho de acurácia da abordagem híbrida sobre as abordagens isoladas, estabeleceu-se um protocolo de **Benchmark Triplo** confrontando:
1. **Modelo White-Box Puro (FPM Clássico)**: Resolvedor mecanicista de balanço populacional operando exclusivamente com a cinética clássica do Núcleo em Diminuição (SCM com constante intrínseca de Balarini k_s = 18.000 µm/min, sem amortecimento artificial α = 0) acoplado à distribuição numérica RRB ÷ D³;
2. **Modelo Black-Box Puro (DDM Malha Aberta)**: Regressor neural MLP tentando prever a conversão macroscópica X_Zn diretamente a partir do tempo e variáveis operacionais, sem conexão mecanicista com o PBM e sem restrições estequiométricas de Herbst;
3. **Modelo Híbrido Serial Campeão (MLP → PBM)**: O acoplamento serial proposto com restrições termodinâmicas garantidas.

O desempenho preditivo foi quantificado através de quatro métricas estatísticas formais (Montgomery; Runger, 2010), avaliadas estritamente sobre a malha temporal ativa (t > 0):

```
Coeficiente de Determinação:     R² = 1 - [ ∑_{i=1}^N (y_exp,i - y_pred,i)² ] / [ ∑_{i=1}^N (y_exp,i - y_medio)² ]
Raiz do Erro Quadrático Médio:   RMSE = √[ (1 / N) · ∑_{i=1}^N (y_exp,i - y_pred,i)² ]
Erro Médio Absoluto:             MAE = (1 / N) · ∑_{i=1}^N |y_exp,i - y_pred,i|
Erro Máximo Pontual:             MaxError = max_i |y_exp,i - y_pred,i|
```

---

## 4.10. Metodologia de Transfer Learning e Validação Externa (Tese de Júlio Cezar Balarini)

### 4.10.1. A Base de Dados Independente de Balarini (UFMG, 2009/2025)
Para atestar a generalização do modelo fora do domínio de calibração (*Out-of-Distribution* — OOD), a modelagem híbrida foi submetida a validação cruzada externa independente sobre a base experimental da tese de doutorado de **Júlio Cezar Balarini (UFMG, 2009 / Revista Observatorio, 2025)**.

Ambos os autores (Bortot Coelho, 2017 e Balarini, 2009) investigaram rigorosamente a lixiviação ácida sulfúrica do **mesmo concentrado mineral industrial** (calcina de zinco da Nexa Resources de Três Marias/Juiz de Fora). Contudo, a base de dados de Balarini (2009) foi conduzida sob condições operacionais e analíticas completamente distintas, constituindo um teste de estresse de alto nível:
- **176 pontos experimentais independentes**, distribuídos em **16 séries cinéticas completas** de lixiviação;
- **Estresse Térmico Multitemperatura**: Ensaios executados em 5 temperaturas distintas (30 °C, 40 °C, 50 °C, 60 °C e 70 °C), enquanto os dados de bancada de Bortot Coelho operaram unicamente a 40 °C;
- **Frações Granulométricas Estreitas Monodispersas**: Ensaios com 6 frações granulométricas separadas por peneiramento Tyler contínuo (-60# a +400#, diâmetros nominais médios de partícula d_p variando entre 40 µm e 180 µm), permitindo avaliar a convolução populacional do PBM sob ausência de polidispersão;
- **Estresse Hidrodinâmico de Agitação Mecânica**: Ensaios conduzidos sob 5 rotações do impelidor (270, 510, 660, 840 e 1080 rpm), adentrando o regime com resistência de filme líquido externo.

---

### 4.10.2. Metodologia de Transfer Learning com Fator de Escala de Área Superficial
Como a bancada de Balarini operou com aparato experimental próprio (reator de geometria distinta, volume de 1000 mL e razões sólido/líquido diluídas de 10 g/L), a densidade de sítios reacionais efetivos por unidade de volume difere por um fator de escala de transferência interlaboratorial.

Para transpor o modelo híbrido calibrado na bancada de Bortot Coelho para o aparato de Balarini sem reajustar os pesos internos da rede neural, formulou-se um procedimento de **Transfer Learning** baseado em um único parâmetro físico multiplicativo de escala de área interfacial efetiva:

```
|v_Balarini(t)| = s_opt · |v_hibrido(t; C_A0, η, t)|
```

sendo s_opt estimado por regressão global unidimensional sobre a condição de referência isotérmica a 40 °C (s_opt ≈ 0,182), mantendo-se a estrutura interna do MLP congelada.

---

### 4.10.3. Modelagem do Estresse Térmico via Lei de Arrhenius Integrada
A dependência térmica da velocidade linear de dissolução foi modelada fenomenologicamente acoplando-se a Lei de Arrhenius clássica à taxa de retração interfacial do modelo híbrido:

```
|v(t, T)| = |v(t, T_ref)| · exp[ - ( E_a / R ) · ( 1/T - 1/T_ref ) ]
```

onde:
- T_ref = 313,15 K (40,0 °C);
- R = 8,314 J · mol⁻¹ · K⁻¹ (constante universal dos gases);
- E_a: energia de ativação aparente de dissolução heterogênea (J/mol).

A energia de ativação aparente do concentrado mineral foi estimada pela linearização de Arrhenius sobre as taxas cinéticas de Balarini (2009):

```
ln(k_ap) = ln(A_0) - ( E_a / R ) · ( 1 / T )
```

obtendo-se **E_a = 22,69 kJ/mol** com coeficiente de correlação extraordinário **R² = 0,9993**. O valor obtido (E_a entre 20 e 40 kJ/mol) confirma que, sob regimes de moderada acidez e em temperaturas intermediárias, o processo heterogêneo atua na zona mista com forte contribuição difusiva através da camada porosa superficial residual.

---

### 4.10.4. Modelagem Granulométrica Monodispersa e Efeito Hidrodinâmico de Filme
1. **Convolução Granulométrica Monodispersa no PBM**: Para as séries de corte granulométrico de Balarini com partículas calibradas em peneiras Tyler, a distribuição contínua RRB foi substituída pela função impulso de Dirac centrada no diâmetro médio da classe granulométrica: q_0(D) = δ_Dirac(D - d_{p,j}), com d_{p,j} ∈ {40, 50, 75, 105, 150, 180} µm. O resolvedor PBM reduz-se analiticamente à retração homogênea:
   X_Zn(t) = 1 - [ max( 0, 1 - δ(t) / d_{p,j} ) ]³
2. **Efeito Hidrodinâmico de Filme Líquido (Rotação do Agitador)**: Nas rotações inferiores a 840 rpm (regimes com N = 270 e 510 rpm), a taxa de extração sofre retardamento decorrente da resistência à difusão mássica externa na camada limite do líquido. Essa atenuação foi modelada acoplando-se um fator hidrodinâmico de filme f_rpm(N):
   f_rpm(N) = min[ 1,0; ( N / N_crit )^0,6 ]
   onde N_crit = 840 rpm representa a velocidade crítica de transição hidrodinâmica acima da qual o coeficiente convectivo de transferência de massa atinge o platô asintótico, tornando a taxa estritamente independente da intensidade de turbulência.

---

## 4.11. Governança Computacional, Reprodutibilidade e Testes Automatizados

Para garantir a transparência científica, rastreabilidade e reprodutibilidade integral dos resultados reportados, toda a pipeline de código e simulação computacional foi desenvolvida sob rigorosos padrões de governança de software em Engenharia Química (*Clean Code* e *DevOps Científico*):
- **Linguagem e Ambiente**: Python 3.11.9 de 64 bits, utilizando as bibliotecas de computação científica `NumPy` 1.26.4, `SciPy` 1.13.1, `Pandas` 2.2.2, `PyTorch` 2.4.1 (com aceleração de autograd) e `Scikit-Learn` 1.5.1;
- **Arquitetura Modular**: O código-fonte organiza-se em módulos ortogonais desacoplados:
  - `etapa0_analise_dados`: Scripts de importação, limpeza e análise estatística dos ensaios de bancada e piloto;
  - `etapa1_modulo_cinetico`: Formulação das equações analíticas do SCM, do Balanço de Herbst e do resolvedor mecanicista `BatchPBMSolver`;
  - `etapa2_otimizacao_inversa`: Rotinas de calibração inversa bi-exponencial e geração de alvos supervisionados;
  - `etapa3_modelagem_ddm`: Classes e pipelines de treinamento, validação cruzada, destilação de redes e seleção MCDA dos 4 modelos Black-Box;
  - `etapa4_modelo_hibrido`: Orquestrador serial do modelo híbrido acoplado e rotinas de benchmark triplo in-domain;
  - `etapa5_validacao_externa`: Rotinas de transfer learning e teste OOD sobre os dados da tese de Júlio Balarini;
- **Determinismo e Controle de Sementes**: Fixação universal da semente do gerador de números pseudoaleatórios em `seed = 42` em todos os algoritmos estocásticos (divisão de dobras, inicialização de pesos de redes neurais e particionamento de árvores);
- **Conjunto de Testes Automatizados (`pytest`)**: Uma bateria exaustiva de **66 testes unitários e de integração contínua** foi desenvolvida e executada, cobrindo:
  1. Conservação estrita de massa e não-negatividade de concentrações e conversões (0 ≤ X_Zn ≤ 1, C_Af ≥ 0);
  2. Normalização de probabilidade da distribuição numérica RRB ÷ D³ (∫ q_0(D) dD = 1,0000 ± 0,0001);
  3. Condição inicial estrita hardcoded em t = 0 (X_Zn(0) = 0, δ(0) = 0);
  4. Monotonicidade temporal de retração (dδ/dt ≥ 0);
  5. Cálculo das derivadas analíticas de `torch.autograd`.
  Todos os 66 testes unitários alcançaram 100% de aprovação (*66 passed in 12.4s*), assegurando a integridade matemática da solução.

---

## 4.12. Referências Bibliográficas Normatizadas

1. ASTER, R. C.; BORCHERS, B.; THURBER, C. H. **Parameter Estimation and Inverse Problems**. 3. ed. Amsterdam: Elsevier / Academic Press, 2018. 408 p.
2. BALARINI, J. C. **Modelagem e Simulação da Lixiviação de Concentrado de Zinco Ustulado em Reatores Contínuos**. 2009. 182 f. Tese (Doutorado em Engenharia Metalúrgica e de Minas) — Escola de Engenharia, Universidade Federal de Minas Gerais, Belo Horizonte, 2009.
3. BALARINI, J. C. Estudo cinético da lixiviação de concentrado de zinco ustulado em escala de bancada. **Revista Observatorio**, Belo Horizonte, v. 11, n. 3, p. 1-28, 2025.
4. BENNET, J. G. Broken coal. **Journal of the Institute of Fuel**, London, v. 10, n. 49, p. 22-39, 1936.
5. BORTOT COELHO, F. **Lixiviação de um Concentrado Ustulado de Zinco em Bancada e em Escala Piloto**. 2017. 187 f. Dissertação (Mestrado em Engenharia Metalúrgica, Materiais e de Minas) — Escola de Engenharia, Universidade Federal de Minas Gerais, Belo Horizonte, 2017.
6. BORTOT COELHO, F. et al. Modeling of zinc calcine leaching in continuous stirred tank reactors. **Hydrometallurgy**, Amsterdam, v. 195, p. 105389, 2020.
7. BREIMAN, L. Random Forests. **Machine Learning**, Boston, v. 45, n. 1, p. 5-32, 2001.
8. CHEN, T.; GUESTRIN, C. XGBoost: A Scalable Tree Boosting System. In: ACM SIGKDD INTERNATIONAL CONFERENCE ON KNOWLEDGE DISCOVERY AND DATA MINING, 22., 2016, San Francisco. **Proceedings [...]** New York: ACM, 2016. p. 785-794.
9. ELGERSMA, F. et al. The selective dissolution of zincite from zinc calcine. **Hydrometallurgy**, Amsterdam, v. 29, n. 1-3, p. 173-189, 1992.
10. GOODFELLOW, I.; BENGIO, Y.; COURVILLE, A. **Deep Learning**. Cambridge: MIT Press, 2016. 800 p.
11. HENDRYCKS, D.; GIMPEL, K. Gaussian Error Linear Units (GELUs). **arXiv preprint**, Ithaca, arXiv:1606.08415, 2016.
12. HERBST, J. A. Rate processes in hydrometallurgy. In: SME-AIME ANNUAL MEETING, 1979, New Orleans. **Proceedings [...]** New York: AIME, 1979. p. 53-112.
13. LEBLANC, S. E.; FOGLER, H. S. Population balance modeling of the dissolution of polydisperse solids. **AIChE Journal**, Hoboken, v. 33, n. 1, p. 54-63, 1987.
14. LEVENSPIEL, O. **Chemical Reaction Engineering**. 3. ed. New York: John Wiley & Sons, 1999. 684 p.
15. LOSHCHILOV, I.; HUTTER, F. Decoupled Weight Decay Regularization. In: INTERNATIONAL CONFERENCE ON LEARNING REPRESENTATIONS (ICLR), 7., 2019, New Orleans. **Proceedings [...]** Amherst: ICLR, 2019. p. 1-18.
16. LUZ, A. B.; SAMPAIO, J. A.; FRANÇA, S. C. A. **Tratamento de Minérios**. 5. ed. Rio de Janeiro: Centro de Tecnologia Mineral (CETEM/MCTI), 2010. 944 p.
17. MONTGOMERY, D. C.; RUNGER, G. C. **Applied Statistics and Probability for Engineers**. 5. ed. New York: John Wiley & Sons, 2010. 784 p.
18. RANDOLPH, A. D.; LARSON, M. A. **Theory of Particulate Processes: Analysis and Techniques of Continuous Crystallization**. 2. ed. San Diego: Academic Press, 1988. 369 p.
19. ROSIN, P.; RAMMLER, E. The Laws Governing the Fineness of Powdered Coal. **Journal of the Institute of Fuel**, London, v. 7, p. 29-36, 1933.
20. SMOLA, A. J.; SCHÖLKOPF, B. A tutorial on support vector regression. **Statistics and Computing**, Dordrecht, v. 14, n. 3, p. 199-222, 2004.
21. SOLLE, D. et al. Between the poles: Some perspectives on hybrid modeling in bioprocess engineering. **Journal of Biotechnology**, Amsterdam, v. 242, p. 81-93, 2017.
22. SZEKELY, J.; EVANS, J. W.; SOHN, H. Y. **Gas-Solid Reactions**. New York: Academic Press, 1976. 400 p.
23. TARANTOLA, A. **Inverse Problem Theory and Methods for Model Parameter Estimation**. Philadelphia: SIAM, 2005. 352 p.
24. VON STOSCH, M. et al. Hybrid modeling for improved extrapolation and transfer learning in the bioprocess industry. **Computers & Chemical Engineering**, Amsterdam, v. 67, p. 119-130, 2014.
