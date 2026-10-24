# 4. MATERIAIS E MÉTODOS

## 4.1. Procedimentos Experimentais e Levantamento da Base de Dados

Nesta subseção são descritos a matéria-prima empregada, os sistemas experimentais de bancada e piloto, os protocolos analíticos de quantificação química, os equacionamentos de cálculo mássico e os critérios de estruturação da base de dados empírica. O trabalho fundamenta-se nos dados experimentais reportados na dissertação de mestrado de Bortot Coelho (2017), desenvolvida no Departamento de Engenharia Metalúrgica e de Materiais da Universidade Federal de Minas Gerais (UFMG), complementados por parâmetros físico-químicos e cinéticos estabelecidos na tese de doutorado de Balarini (2009) e em estudos correlatos da literatura hidrometalúrgica. A metodologia foi estruturada de modo a padronizar e condicionar os dados para a calibração do modelo mecanicista de balanço populacional e para o treinamento supervisionado dos modelos orientados por dados.

---

### 4.1.1. Matéria-Prima e Protocolos de Caracterização da Calcina de Zinco

A matéria-prima utilizada nos experimentos foi o concentrado ustulado de zinco (comercialmente designado como calcina de zinco), obtido pela ustulação oxidante em leito fluidizado de concentrados sulfetados na unidade industrial de Três Marias (MG) da Nexa Resources (Bortot Coelho, 2017). Para garantir a representatividade das alíquotas experimentais e prevenir segregação por tamanho de partícula durante o manuseio, o lote de material bruto foi submetido a homogeneização física e quarteamento sequencial pela técnica de pilha cônica (Luz; Sampaio; França, 2010).

Os procedimentos analíticos e instrumentais empregados na caracterização física, mineralógica e química da calcina compreenderam as seguintes metodologias:

a) **Picnometria de líquidos**: A densidade real das partículas sólidas foi obtida por picnometria de líquidos utilizando picnômetro de vidro de 50 mL calibrado com água destilada desaerada a 25 °C. A determinação experimental estabeleceu a densidade real média em 5,61 g·cm⁻³, valor utilizado para o cálculo da densidade molar da zincita sólida pura (ρ_s = 69,2 mol·L⁻¹), parâmetro volumétrico fundamental para a resolução do Balanço Populacional (Balarini, 2009; Bortot Coelho, 2017).

b) **Difração de Raios X (DRX)**: A determinação das fases cristalinas constituintes foi conduzida em difratômetro Empyrean da PANalytical, com radiação Cu-Kα (λ = 1,5406 Å) e detector proporcional de Xe selado em amostras moídas abaixo de 63 μm (230# Tyler). A identificação das reflexões cristalográficas foi realizada com o auxílio do software HighScore e da biblioteca de difração de pós, permitindo identificar as fases mineralógicas presentes: zincita (ZnO, fase majoritária solúvel), ferrita de zinco (ZnFe₂O₄, fase secundária refratária), willemita (Zn₂SiO₄), quartzo (SiO₂) e esfalerita não-ustulada (ZnS).

c) **Fluorescência de Raios X (FRX)**: Realizada em espectrômetro por dispersão de comprimento de onda (FRX-WDS), modelo PW2400 da Philips, para levantamento semiquantitativo dos elementos majoritários e minoritários presentes na matriz sólida.

d) **Espectrofotometria de Absorção Atômica (EAA)**: Para quantificação elementar dos metais totais, amostras quarteadas foram submetidas a digestão ácida total com água-régia (mistura concentrada de HNO₃ e HCl na proporção 1:3 v/v) sob refluxo e aquecimento contínuo em ebulição até solubilização completa da matriz inorgânica. Os licores resultantes foram filtrados, avolumados e analisados em espectrofotômetro de absorção atômica de chama (modelo XPlorAA, GBC Scientific Equipment). Esse procedimento quantificou os teores totais de zinco (61,2% m/m) e de ferro (5,8% m/m) na calcina.

e) **Lixiviação seletiva amoniacal**: Como a ferrita de zinco e os sulfetos residuais não se dissolvem em meio ácido brando, adotou-se o método de lixiviação seletiva amoniacal estabelecido por Elgersma et al. (1992) para quantificar exclusivamente a fração de zinco presente como óxido livre (zincita, ZnO). Amostras de calcina foram lixiviadas por duas horas a 25 °C em solução contendo 150 g·L⁻¹ de NH₃ e 20 g·L⁻¹ de NH₄Cl sob agitação contínua. A dosagem de zinco no licor amoniacal por EAA permitiu estabelecer a fração mássica de zincita na calcina em T_ZnO = 76,1% (base seca), parâmetro estequiométrico que rege todos os cálculos mássicos e cinéticos subsequentes.

f) **Análise de distribuição granulométrica**: A determinação do espectro granulométrico das partículas do concentrado original foi executada pela combinação de peneiramento a úmido para as frações grossas e difração a laser para as frações finas (Bortot Coelho, 2017, Capítulo 5), conforme formulado e modelado detalhadamente na Subseção 4.3.

---

### 4.1.2. Sistema Experimental e Procedimentos de Bancada (Batelada)

Os ensaios cinéticos descontínuos foram realizados no aparato de lixiviação de bancada esquematizado na dissertação de Bortot Coelho (2017, Capítulo 4). O sistema experimental foi dimensionado com base nos seguintes critérios:

- **Reator encamisado**: Reator cilíndrico de vidro borossilicato com fundo semiesférico encamisado, com volume nominal de 500 mL, operado com volume constante de solução lixiviante de V = 400 mL (0,400 L). A tampa do reator dispunha de quatro bocas esmerilhadas vedadas para acoplamento do agitador, eletrodo de pH, condensador de refluxo para evitar perdas por evaporação e cânula de amostragem de polpa;
- **Controle térmico**: A temperatura reacional foi fixada em T = 40 °C ± 0,5 °C em todos os ensaios, assegurada pela circulação de água termostatizada por banho ultratermostático microprocessado (modelo Fuzzy, Thermo Fisher Scientific) conectado à camisa externa do reator;
- **Agitação mecânica**: Promovida por agitador mecânico de haste com impelidor tipo turbina de pás planas retas (diâmetro de 35 mm, posicionado a um terço da altura do fundo do reator), operando a 1000 rpm. A justificativa metodológica para a fixação dessa rotação reside na necessidade de garantir que o sistema opere acima da velocidade crítica de suspensão de sólidos e em regime turbulento pleno, eliminando a resistência à transferência de massa no filme líquido externo que envolve as partículas sólidas (Bortot Coelho, 2017);
- **Instrumentação analítica**: Medição em tempo real do pH inicial da solução ácida e do pH final do licor por meio de eletrodo combinado de vidro conectado a medidor Denver Instrument (modelo 220).

O reagente lixiviante utilizado foi o ácido sulfúrico (H₂SO₄ P.A., pureza de 98% m/m, densidade 1,84 g·cm⁻³, Merck), diluído em água destilada para a obtenção das concentrações planejadas.

---

### 4.1.3. Planejamento Fatorial e Cálculo da Carga Reacional de Bancada

Para avaliar o comportamento reacional sob diferentes disponibilidades de ácido em relação ao sólido, adotou-se um planejamento experimental fatorial completo 4×4, combinando quatro níveis de concentração inicial de ácido sulfúrico (C_A0) e quatro níveis de razão molar estequiométrica (η), totalizando 16 ensaios executados em triplicata autêntica (Bortot Coelho, 2017, Apêndice A1.1).

A razão molar estequiométrica η quantifica a proporção entre a quantidade de matéria inicial de ácido sulfúrico adicionada na fase líquida (n_A0) e a quantidade de matéria inicial de zincita contida na massa de calcina introduzida (n_B0), calculada pela Equação (4.1):

η = n_A0 / n_B0 = (V · C_A0) / [ (m_B0 · T_ZnO) / MM_ZnO ]                                         (4.1)

sendo V o volume de solução lixiviante (0,400 L), C_A0 a concentração inicial de H₂SO₄ (mol·L⁻¹), m_B0 a massa inicial de calcina introduzida no reator (g), T_ZnO a fração mássica de zincita na calcina (0,761) e MM_ZnO a massa molar da zincita (81,38 g·mol⁻¹). A partir do rearranjo algébrico da Equação (4.1), determinou-se a massa exata de calcina m_B0 adicionada em cada ensaio para fixar o valor de η desejado, conforme a Equação (4.2):

m_B0 = (V · C_A0 · MM_ZnO) / (η · T_ZnO)                                                             (4.2)

Os níveis operacionais investigados compreenderam:
- **Concentração inicial de ácido**: C_A0 = 0,10; 0,50; 1,00 e 1,50 mol·L⁻¹ (equivalentes a 10, 50, 100 e 150 g·L⁻¹ de H₂SO₄, representando as faixas de acidez praticadas nas etapas industriais de lixiviação neutra e ácida);
- **Razão molar estequiométrica**: η = 0,5 (deficiência estequiométrica, ácido limitante); 1,0 (proporção equimolar estequiométrica); 1,5 (excesso moderado de +50%); e 3,1 (forte excesso de +210%).

A metodologia de ajuste da massa sólida m_B0 implicou a variação sistemática da densidade de polpa entre 3,0 g·L⁻¹ e 300,0 g·L⁻¹. A matriz experimental correspondente, com as condições operacionais e as massas calculadas por esse procedimento, encontra-se consolidada na Tabela 4.1.

**Tabela 4.1 – Matriz do planejamento experimental fatorial 4×4 dos ensaios de lixiviação em batelada (Bortot Coelho, 2017).**

| Ensaio | Razão Molar η (-) | C_A0 (mol·L⁻¹) | m_B0 (g) | Razão S/L (g·L⁻¹) | Classificação Estequiométrica |
|:------:|:-----------------:|:--------------:|:--------:|:-----------------:|:------------------------------|
| 1      | 0,5               | 0,10           | 8,6      | 21,4              | Reagente ácido limitante      |
| 2      | 0,5               | 0,50           | 42,8     | 106,9             | Reagente ácido limitante      |
| 3      | 0,5               | 1,00           | 85,6     | 213,9             | Reagente ácido limitante      |
| 4      | 0,5               | 1,50           | 120,0    | 300,0             | Reagente ácido limitante      |
| 5      | 1,0               | 0,10           | 4,3      | 10,7              | Proporção estequiométrica 1:1 |
| 6      | 1,0               | 0,50           | 21,4     | 53,5              | Proporção estequiométrica 1:1 |
| 7      | 1,0               | 1,00           | 42,8     | 106,9             | Proporção estequiométrica 1:1 |
| 8      | 1,0               | 1,50           | 64,2     | 160,4             | Proporção estequiométrica 1:1 |
| 9      | 1,5               | 0,10           | 2,9      | 7,1               | Excesso moderado (+50%)       |
| 10     | 1,5               | 0,50           | 14,3     | 35,6              | Excesso moderado (+50%)       |
| 11     | 1,5               | 1,00           | 28,5     | 71,3              | Excesso moderado (+50%)       |
| 12     | 1,5               | 1,50           | 42,8     | 106,9             | Excesso moderado (+50%)       |
| 13     | 3,1               | 0,10           | 1,3      | 3,2               | Forte excesso (+210%)         |
| 14     | 3,1               | 0,50           | 6,9      | 17,2              | Forte excesso (+210%)         |
| 15     | 3,1               | 1,00           | 13,8     | 34,5              | Forte excesso (+210%)         |
| 16     | 3,1               | 1,50           | 20,7     | 51,7              | Forte excesso (+210%)         |

*Fonte: Adaptado de Bortot Coelho (2017, Apêndice A1.1, Tabela A1.1).*

---

### 4.1.4. Métodos de Amostragem, Determinação Química e Tratamento de Incertezas

A condução experimental dos ensaios de bancada e o protocolo analítico de quantificação foram padronizados de acordo com as seguintes etapas metodológicas:

1. **Condicionamento térmico inicial**: O volume de 400 mL de solução sulfúrica na concentração C_A0 desejada foi adicionado ao reator. O sistema foi vedado, acionou-se a agitação mecânica a 1000 rpm e aguardou-se a completa estabilização térmica em 40 °C ± 0,5 °C via banho ultratermostático;
2. **Introdução da carga sólida**: A massa calculada de calcina m_B0 foi adicionada instantaneamente ao reator por funil de vidro seco, acionando-se o cronômetro no momento da introdução (instante t = 0);
3. **Amostragem temporal com interrupção instantânea**: Alíquotas de polpa de 3 a 5 mL foram retiradas nos tempos predeterminados: t = 0,5; 1; 2; 3; 4; 5 e 15 minutos. A coleta foi realizada por micropipeta calibrada de 1000 μL acoplada a filtro de membrana de acetato de celulose com abertura de poro de 0,45 μm. A retenção imediata dos sólidos na membrana interrompeu a dissolução heterogênea no instante exato da amostragem, evitando que a reação continuasse ocorrendo fora do reator;
4. **Quantificação de Zn e Fe no licor**: As alíquotas líquidas filtradas foram acidificadas com HNO₃ a 2% (v/v) para estabilização dos íons metálicos em balões volumétricos e analisadas por EAA de chama no espectrofotômetro XPlorAA para determinação das concentrações totais de zinco (C_Zn,t) e de ferro (C_Fe,t) em solução;
5. **Titulação da acidez livre residual (C_Af)**: Ao final do ensaio (t = 15 min), a polpa remanescente foi filtrada a vácuo em papel filtro faixa azul. Uma alíquota do filtrado límpido foi titulada com solução padronizada de NaOH (0,1 ou 1,0 mol·L⁻¹), empregando citrato de sódio como agente mascarante para complexar os cátions metálicos (Zn²⁺ e Fe³⁺), impedindo a precipitação prematura de seus hidróxidos e garantindo a titulação seletiva dos íons H⁺ livres;
6. **Dedução da conversão fracionária de zincita (X_Zn)**: Sabendo que o ferro solubilizado decorre exclusivamente da lixiviação estequiométrica da ferrita de zinco (ZnFe₂O₄, com razão molar Zn:Fe = 1:2), a concentração de zinco originada unicamente da dissolução da zincita (C_Zn,ZnO) foi isolada analiticamente pela Equação (4.3):

C_Zn,ZnO(t) = C_Zn,t(t) - (1/2) · C_Fe,t(t) · (MM_Zn / MM_Fe)                                       (4.3)

A conversão fracionária de zincita X_Zn(t) foi então calculada relacionando a massa de zinco solubilizada proveniente da zincita com a massa teórica máxima de zinco contida na carga inicial de zincita, conforme expressa a Equação (4.4):

X_Zn(t) = [ V · C_Zn,ZnO(t) ] / [ (m_B0 · T_ZnO · MM_Zn) / MM_ZnO ]                               (4.4)

7. **Tratamento estatístico de incertezas**: Todos os 16 ensaios foram conduzidos em triplicata autêntica e independente (n = 3). O tratamento de incertezas baseou-se na estimativa do intervalo de confiança para a média de uma distribuição normal com variância desconhecida, calculado por meio da distribuição t de Student (Montgomery; Runger, 2010), conforme a Equação (4.5):

IC_95% = X̄_Zn ± [ (t_α/2; n-1 · σ) / √n ]                                                          (4.5)

sendo X̄_Zn a média amostral da conversão, σ o desvio padrão amostral e t_0,025; 2 = 3,182 o parâmetro crítico da distribuição t com n − 1 = 2 graus de liberdade e nível de significância α = 0,05 (correspondente a 95% de confiança). Esse critério permitiu atribuir barras de erro padronizadas a cada medição temporal.

---

### 4.1.5. Sistema Experimental de Lixiviação Contínua em Planta Piloto

Para a subsequente etapa de validação em escala contínua e avaliação da capacidade de generalização e transferência de aprendizado (*transfer learning*) dos modelos desenvolvidos, foram adotados os dados experimentais da planta piloto de lixiviação contínua operada por Bortot Coelho (2017, Apêndice A1.2) e publicada em Bortot Coelho et al. (2020).

O aparato contínuo foi estruturado como uma cascata de três reatores contínuos de mistura perfeita (CSTR) dispostos em série, cada um com volume útil de 6,0 L (volume reacional total de 18,0 L). A dosagem contínua de calcina foi realizada por tremonha com prato circular giratório acionado por motor elétrico de velocidade regulável e raspador mecânico calibrado; a alimentação de solução ácida (C_A0 = 0,50 mol·L⁻¹) foi suprida no primeiro reator por bomba peristáltica de alta precisão (modelo Qdos 30, Watson-Marlow). O escoamento entre os três reatores deu-se por transbordo gravitacional em canaletas laterais. A temperatura foi mantida em 40 °C e a agitação mecânica em 500 rpm em todos os estágios, com razão molar estequiométrica global de alimentação fixada em η = 1,0.

A metodologia piloto compreendeu a investigação de duas condições hidrodinâmicas contrastantes:
- **Condição Piloto 1 (vazão intermediária)**: Vazão volumétrica de 0,41 L·min⁻¹, resultando em tempo de residência espacial médio de τ_i = 14,6 min por reator (tempo total da cascata de 43,9 min), acompanhada temporalmente durante o período transiente entre t = 45 e 150 min (Bortot Coelho, 2017, Tabela A1.6);
- **Condição Piloto 2 (vazão reduzida)**: Vazão volumétrica de 0,21 L·min⁻¹, resultando em tempo de residência espacial médio de τ_i = 28,6 min por reator (tempo total de 85,7 min), acompanhada entre t = 90 e 300 min (Bortot Coelho, 2017, Tabela A1.7).

Em ambas as condições, o protocolo experimental consistiu no acompanhamento temporal transiente até a consolidação do estado estacionário para as variáveis: conversão de zinco por reator (X_Zn,R1, X_Zn,R2, X_Zn,R3), concentração residual de ácido livre (C_Af,R1, C_Af,R2, C_Af,R3) e teores de ferro solubilizado.

---

### 4.1.6. Estruturação e Proveniência Metodológica da Base de Dados

Para possibilitar a execução das rotinas computacionais em ambiente Python e garantir a reprodutibilidade dos cálculos em conformidade com as diretrizes FAIR (*Findable, Accessible, Interoperable, and Reusable*), os dados empíricos originais foram organizados em estruturas tabulares padronizadas. A proveniência acadêmica e a finalidade metodológica de cada conjunto de dados são estabelecidas a seguir:

a) **Trajetórias cinéticas transientes de bancada**: Extraída da Tabela A1.4 do Apêndice A1.1 da dissertação de Bortot Coelho (2017, p. 201). Compreende 128 observações experimentais correspondentes à média das triplicatas de conversão de zincita nos 8 pontos temporais (t = 0 a 15 min) para os 16 ensaios. Os dados foram estruturados em formato longo (*tidy format*) com as variáveis ensaio, η, C_A0, t e X_Zn, viabilizando o fatiamento temporal, a calibração de parâmetros dinâmicos e o treinamento supervisionado dos modelos;

b) **Condições finais de equilíbrio e balanço de bancada**: Extraída da Tabela A1.1 do Apêndice A1.1 da dissertação de Bortot Coelho (2017, p. 200). Reúne as condições iniciais de carga (massas, volumes, concentrações, razões sólido/líquido) e os estados finais medidos em t = 15 min (pH final, acidez livre residual C_Af, conversões finais de Zn e Fe), empregados para verificação de balanços globais e validação de patamares assintóticos;

c) **Dados cinéticos contínuos da planta piloto**: Extraídos das Tabelas A1.6 e A1.7 do Apêndice A1.2 da dissertação de Bortot Coelho (2017, p. 202) e de Bortot Coelho et al. (2020). Reúnem as séries temporais transientes dos três CSTRs em cascata, reservadas para o segundo estágio de validação dos modelos e testes de extrapolação entre escalas;

d) **Caracterização granulométrica da calcina**: Extraída da Tabela 5.4 (Capítulo 5, p. 129) e do Apêndice A3 de Bortot Coelho (2017). Compreende a fração mássica acumulada de sólidos passante obtida pela combinação de peneiramento a úmido (malhas 38 a 297 μm) e difração a laser (faixa de 0,45 a 74 μm), utilizada na calibração da função de distribuição granulométrica inicial (Subseção 4.3);

e) **Parâmetros constitutivos e cinéticos de referência**: A constante cinética intrínseca superficial (k_s = 1,8 × 10⁴ μm·min⁻¹) e a ordem de reação em relação ao ácido (n = 0,7) foram obtidas a partir da tese de doutorado de Balarini (2009, p. 115) e de Balarini et al. (2008, 2025). O parâmetro estático de ajuste do balanço populacional de bancada (α = 5,5 × 10³ μm·min⁻¹) foi obtido na dissertação de Bortot Coelho (2017, Tabela 5.9, p. 155).
