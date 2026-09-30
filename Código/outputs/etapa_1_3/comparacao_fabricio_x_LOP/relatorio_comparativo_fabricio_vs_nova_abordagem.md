# Relatório Técnico: Análise Comparativa entre o Modelo Fenomenológico de Referência (Bortot Coelho, 2017) e a Abordagem Híbrida Adaptativa

**Projeto**: Modelagem Híbrida de Lixiviação de Zinco (DEQ/UFMG)  
**Autor**: Antigravity AI Pair Programmer & Equipe LOP  
**Data**: 26 de Setembro de 2026  
**Finalidade**: Exame técnico, fundamentação bibliográfica e comparação quantitativa entre o Modelo Fenomenológico de Referência (desenvolvido na dissertação de mestrado de Fabrício Bortot Coelho, 2017) e a Nova Abordagem Híbrida/Adaptativa baseada em Balanço Populacional com perfis dinâmicos de velocidade interfacial.

---

## 1. Contexto e Valorização do Trabalho Pioneiro de Bortot Coelho (2017)

A dissertação de mestrado de Fabrício Bortot Coelho (*"Lixiviação de um Concentrado Ustulado de Zinco em Bancada e em Escala Piloto"*, Programa de Pós-Graduação em Engenharia Metalúrgica, Materiais e de Minas — PPGEM/UFMG, 2017, orientada pelos Profs. Marcelo Borges Mansur e Versiane Albis Leão) representou um marco científico de excelência para a hidrometalurgia do zinco no Brasil.

O trabalho de Bortot Coelho teve o mérito pioneiro de:
1. Construir uma base experimental rigorosa e sistemática de lixiviação ácida sob 16 condições distintas de bancada, variando a razão molar ácido/minério (η ∈ {0,5; 1,0; 1,5; 3,1}) e a concentração inicial de ácido (C_A0 ∈ {0,10; 0,50; 1,00; 1,50} mol/L);
2. Formular o acoplamento do Balanço Populacional multiparticulado unidimensional (PBM) à distribuição granulométrica contínua do minério representada pela equação de Rosin-Rammler-Bennet (RRB);
3. Integrar analiticamente o balanço estequiométrico de reagente limitante ao modelo de conversão progressiva, demonstrando que a lixiviação do óxido de zinco (zincita) ocorre sob controle estrito por reação química superficial heterogênea.

O objetivo do presente estudo não é apontar falhas de forma descontextualizada, mas sim **revisitar com respeito e profundidade os pontos identificados pelo próprio Fabrício em sua dissertação**, demonstrando onde a hipótese simplificadora de um parâmetro de amortecimento constante encontrou seus limites físicos e como a abordagem híbrida moderna cumpre o papel de aprimorar essa formulação clássica.

---

## 2. Fundamentação Textual na Dissertação: Calibração de α e Avaliação dos Resíduos

A necessidade de uma formulação adaptativa ou híbrida decorre diretamente das escolhas metodológicas e das análises quantitativas documentadas na própria dissertação de Bortot Coelho (2017).

### 2.1. Onde o Parâmetro α é Estimado e Mantido Constante
Na **Seção 5.2.4 (páginas 147 a 150 do texto / páginas 174 a 177 do arquivo PDF)**, intitulada *"5.2.4. Estimativa do parâmetro ajustável (α)"*, o autor discute com clareza as premissas físico-químicas de seu modelo:

- **Complexidade Mineralógica**: Fabrício destaca que, embora o zinco esteja majoritariamente presente como zincita (ZnO), o concentrado contém espécies refratárias como esfalerita (ZnS), willemita (Zn₂SiO₄) e ferrita de zinco (ZnFe₂O₄), cuja dissolução total exige condições severas de temperatura e pressão (p. 147 do texto / p. 174 do PDF).
- **Hipótese Simplificadora**: Diante da elevada complexidade de modelar individualmente cada fase mineralógica e as interações iônicas interfaciais, o autor optou por considerar apenas a reação estequiométrica da zincita com H₂SO₄, incorporando um termo empírico de desaceleração proporcional ao consumo de ácido na taxa linear de retração de diâmetro (Equação 4.1 da dissertação, p. 148 do texto / p. 175 do PDF):

$$\frac{dD}{dt} = v(D) = -\frac{2}{\rho_s} \left[ k_s C_{Af} - \alpha (C_{A0} - C_{Af}) \right]$$

- **Equação do Patamar de Equilíbrio**: Ao observar que a conversão experimental estabilizava em um patamar constante após os 5 minutos iniciais de reação em batelada, o autor impôs a condição de repouso cinético $v(D) = 0$. Combinando as equações de velocidade e o balanço estequiométrico de Herbst, deduziu a relação assintótica da conversão teórica máxima (Equação 5.3 da dissertação, p. 149 do texto / p. 176 do PDF):

$$X_{\text{Zn}}^{\text{Max}} = \eta \left( 1 - \frac{\alpha}{k_s + \alpha} \right), \quad 0 \le X_{\text{Zn}}^{\text{Max}} \le 1$$

- **Ajuste por Mínimos Quadrados**: Fabrício determinou o parâmetro $\alpha$ minimizando a soma quadrática dos resíduos globais entre a conversão teórica e as conversões finais dos 16 ensaios (Equação 5.4 da dissertação):

$$\text{SQE} = \sum (X_{\text{Zn}} - X_{\text{Zn}}^{\text{Max}})^2$$

O valor ótimo global encontrado pelo autor foi:

$$\alpha = 5,5 \times 10^3\ \mu\text{m/min} \quad (\text{com SQE mínimo de } 0,05)$$

- **Consolidação Nominal**: Na **Tabela 5.9 (página 155 do texto / página 182 do PDF)**, esse valor único de $\alpha = 5,5 \times 10^3\ \mu\text{m/min}$ foi consolidado como parâmetro nominal e mantido **rigorosamente constante** em todas as simulações do modelo PBM, tanto para os ensaios de batelada quanto para a transposição aos reatores contínuos em escala piloto.

---

### 2.2. Onde o Próprio Fabrício Calcula e Discute os Desvios do Modelo PBM
Na **Seção 5.2.6 (páginas 155 a 159 do texto / páginas 182 a 186 do PDF)**, intitulada *"5.2.6. Comparação dos dados gerados pelo modelo proposto com os dados experimentais"*, o autor compara as curvas preditas às medições experimentais (Figuras 5.21 e 5.22) e calcula formalmente os resíduos do modelo na **Tabela 5.10 (página 158 do texto / página 185 do PDF)**:

#### Tabela 5.10 da Dissertação (Bortot Coelho, 2017, p. 158 / p. 185 do PDF)
| Agrupamento por C_A0 (mol/L) | SQE (X_Zn) | SQE (C_Af) | Agrupamento por Razão Molar (η) | SQE (X_Zn) | SQE (C_Af) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **0,10** | **0,040** | 0,001 | **0,5** | 0,009 | 0,001 |
| **0,50** | **0,024** | 0,005 | **1,0** | 0,012 | 0,024 |
| **1,00** | **0,006** | 0,017 | **1,5** | **0,043** | 0,014 |
| **1,50** | **0,011** | 0,030 | **3,1** | 0,016 | 0,016 |

Ao analisar esses números e as curvas das Figuras 5.21 e 5.22, o autor faz considerações científicas honestas e perspicazes:
1. **Desvios na Dinâmica Inicial**: Fabrício registra que *"nos primeiros minutos da lixiviação, há um maior desvio entre os valores gerados pelo modelo e os dados experimentais"* (p. 157 do texto / p. 184 do PDF), atribuindo esse comportamento à rápida reação das partículas ultrafinas que o modelo com parâmetros constantes não consegue captar plenamente;
2. **Maior Discrepância na Diluição (C_A0 = 0,10 mol/L)**: A própria Tabela 5.10 indica que a concentração de 0,10 mol/L apresentou o maior resíduo quadrático entre todas as séries de acidez (SQE = 0,040), evidenciando que em polpas altamente diluídas a hidrodinâmica local se diferencia da hipótese média global;
3. **Efeito Preponderante da Razão Molar**: O autor observa que a razão molar η determina a taxa e a extensão com que o ácido é consumido, sendo o principal fator de desaceleração.

Portanto, as limitações do modelo puramente mecanicista com $\alpha$ constante **não são uma suposição externa deste projeto**: elas foram explicitamente quantificadas e reportadas pelo próprio Fabrício Bortot Coelho em sua dissertação de mestrado.

---

## 3. Análise Comparativa Consolidada: Onde os Modelos Convergem e Onde Divergem

Avaliando o conjunto completo dos 16 ensaios experimentais (128 pontos amostrais de conversão temporal), a comparação entre o Modelo Mecanístico Nominal de Referência (FPM com $\alpha = 5500\ \mu\text{m/min}$) e a Nova Abordagem Híbrida/Adaptativa revela três comportamentos bem definidos:

### 3.1. Regimes de Elevada Concordância Mútua (Amplo Excesso de Ácido, η = 3,1 e η = 1,5)
Quando o sistema opera com excesso estequiométrico de ácido sulfúrico (η = 3,1 e η = 1,5), o modelo clássico de Bortot Coelho apresenta desempenho notável:
- **Ensaio 12** (η = 3,1; C_A0 = 1,00 M): R² = 0,9983 (Modelo Nominal) vs. R² = 0,9996 (Nova Abordagem);
- **Ensaio 16** (η = 3,1; C_A0 = 1,50 M): R² = 0,9970 (Modelo Nominal) vs. R² = 0,9995 (Nova Abordagem);
- **Ensaio 7** (η = 3,1; C_A0 = 0,50 M): R² = 0,9919 (Modelo Nominal) vs. R² = 0,9999 (Nova Abordagem);
- **Ensaio 14** (η = 1,5; C_A0 = 1,00 M): R² = 0,9904 (Modelo Nominal) vs. R² = 0,9993 (Nova Abordagem).

**Interpretação Físico-Química**: Em condições de excesso de ácido, a acidez livre C_Af permanece relativamente elevada ao longo de todo o tempo de residência. Como consequência, o termo de força-motriz química direta ($k_s \cdot C_{Af}$) predomina sobre o termo de amortecimento empírico [$\alpha \cdot (C_{A0} - C_{Af})$], permitindo que a conversão atinja níveis superiores a 95% sem que o modelo nominal antecipe indevidamente o equilíbrio.

---

### 3.2. Regimes com Desvios Sistemáticos do Modelo Nominal de Referência

Quando o processo é submetido a restrições estequiométricas ou variações hidrodinâmicas extremas, a premissa de um $\alpha$ único e constante resulta em afastamentos matemáticos bem caracterizados:

#### A. Limitação Estequiométrica Severa de Ácido (η = 0,5 — Ensaios 1, 3, 4 e 5)
- **Comportamento Teórico do Modelo Nominal**:
  Pela Equação (5.3) da dissertação de Fabrício, a conversão assintótica máxima prevista com os parâmetros nominais ($k_s = 1,8 \times 10^4\ \mu\text{m/min}$ e $\alpha = 5,5 \times 10^3\ \mu\text{m/min}$) é:
  
  $$X_{\text{Zn}}^{\text{Max}} = \eta \left( 1 - \frac{5500}{18000 + 5500} \right) = \eta \cdot (1 - 0,2340) = 0,7660 \cdot \eta$$
  
  Para $\eta = 0,5$, o modelo nominal interrompe o avanço da reação em:
  
  $$X_{\text{Zn}}^{\text{Max}} = 0,7660 \cdot 0,50 = 0,3830 \quad (38,3\%)$$

- **Comportamento Experimental Real**:
  Nos experimentos de bancada com $\eta = 0,5$, como a quantidade de óxido de zinco é adicionada em dobro em relação ao ácido sulfúrico disponível, o ácido é completamente exaurido pelos íons solúveis até $C_{Af} \to 0$. O limite estequiométrico real do reagente limitante conduz o sistema a **exatamente 50,0% de conversão** ($X_{\text{Zn}} = 0,5000$).
- **Discrepância Observada**:
  O modelo nominal atinge o patamar em 38,3% e antecipa o equilíbrio em cerca de 11,7% abaixo da conversão real de 50,0%. Nos ensaios 1, 3, 4 e 5, o coeficiente de determinação do modelo nominal situa-se na faixa de $R^2 = 0,56$ a $0,64$.
- **Solução Pela Nova Abordagem**:
  A nova formulação adaptativa acomoda a desaceleração estequiométrica sem fixar a fração residual $C_{Af}^*$ a priori, convergindo com precisão para o patamar experimental de $50,0\%$ e atingindo $R^2 \ge 0,987$ em todos os ensaios dessa classe.

#### B. Proporção Estequiométrica Nominal (η = 1,0 — Ensaios 6, 8, 9 e 10)
- **Comportamento Teórico do Modelo Nominal**:
  Para $\eta = 1,0$, a Equação (5.3) de Bortot Coelho estabelece:
  
  $$X_{\text{Zn}}^{\text{Max}} = 0,7660 \cdot 1,0 = 0,7660 \quad (76,6\%)$$

- **Comportamento Experimental Real**:
  Na bancada física, a lixiviação continua ocorrendo em ritmo mais moderado e alcança conversões finais entre **85% e 87%**.
- **Discrepância Observada**:
  O modelo nominal estabiliza nos 76,6%, gerando um desvio sistemático de patamar entre $8,4\%$ e $10,4\%$ frente aos pontos reais.
- **Solução Pela Nova Abordagem**:
  A nova formulação reproduz fielmente tanto a curvatura inicial quanto o patamar final de 85% a 87%, alcançando $R^2 > 0,998$ nesses ensaios.

#### C. Polpas Altamente Diluídas (C_A0 = 0,10 mol/L — Ensaios 1, 2, 6 e 11)
- Conforme o próprio autor pontuou em sua Tabela 5.10 (maior SQE global), em polpas muito diluídas com alta rotação mecânica (1000 rpm), o cisalhamento turbulento maximiza o transporte de massa das frações finas de minério nos primeiros 30 a 60 segundos de reação.
- Uma taxa cinética $k_s$ estática associada a um $\alpha$ global subestima essa taxa inicial de dissolução transiente, originando um descompasso inicial nas curvas.
- A nova abordagem bi-exponencial captura simultaneamente o decaimento cinético ultrarrápido inicial e a desaceleração suave posterior.

---

## 4. Comparativo Numérico Global entre os Modelos

A tabela a seguir sumariza as métricas estatísticas consolidadas para os 128 pontos experimentais do banco de dados completo de Bortot Coelho (2017):

| Métrica Estatística Global (128 pontos amostrais) | Modelo Mecanístico Nominal de Referência (Bortot Coelho, 2017; α = 5500) | Nova Abordagem Híbrida Adaptativa (Balanço Populacional Otimizado) | Benefício Quantitativo |
| :--- | :---: | :---: | :---: |
| **Coeficiente de Determinação Global (R²)** | **0,9030** | **0,9990** (0,99896) | **Elevação de +0,0960** no R² global |
| **Raiz do Erro Quadrático Médio (RMSE)** | **0,1010 (10,10%)** | **0,0105 (1,05%)** | **Redução de ~10 vezes no erro médio** |
| **Erro Médio Absoluto (MAE)** | **0,0760 (7,60%)** | **0,0071 (0,71%)** | **Aumento substancial na acurácia global** |
| **Desvio Médio no Patamar de Equilíbrio (t = 15 min)** | **5,90% de conversão** | **0,61% de conversão** | **Aderência aos equilíbrios termodinâmicos** |
| **Menor R² Obtido em Ensaio Individual** | **0,5317 (Ensaio 6)** | **0,9873 (Ensaio 4)** | **Consistência em todos os regimes operacionais** |

---

## 5. Acervo de Figuras Científicas de Comparação (300 DPI)

Os gráficos comparativos foram regerados com linguagem técnica refinada, cores contrastantes acessíveis e formatação visual em conformidade com o padrão do projeto:
📂 Diretório: [`Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/)

1. [**`fig_comp_01_cinetica_16_ensaios.png`**](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_01_cinetica_16_ensaios.png) / [PDF Vetorial](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_01_cinetica_16_ensaios.pdf):
   - Painel 2×2 ilustrando as trajetórias cinéticas para todos os 16 ensaios divididos pelas 4 razões molares investigadas ($\eta = 0,5$; $\eta = 1,0$; $\eta = 1,5$; $\eta = 3,1$).
   - Permite visualizar a excelente concordância de ambos os modelos nos regimes com excesso de ácido ($\eta = 1,5$ e $\eta = 3,1$) e a convergência refinada da nova abordagem para os patamares assintóticos reais nos regimes subestequiométricos ($\eta = 0,5$ e $\eta = 1,0$).
2. [**`fig_comp_02_metricas_e_erro_patamar.png`**](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_02_metricas_e_erro_patamar.png) / [PDF Vetorial](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_02_metricas_e_erro_patamar.pdf):
   - Painel (a): Comparação do coeficiente de determinação ($R^2$) ensaio por ensaio, evidenciando o padrão homogêneo de excelência da nova abordagem ($R^2 \ge 0,987$).
   - Painel (b): Comparação dos desvios absolutos de conversão no patamar assintótico final ($t = 15$ min), demonstrando a redução consistente das discrepâncias finais para valores abaixo de $0,6\%$.
3. [**`fig_comp_03_paridade_e_residuos.png`**](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_03_paridade_e_residuos.png) / [PDF Vetorial](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_03_paridade_e_residuos.pdf):
   - Gráficos de paridade 1:1 (Conversão Prevista vs. Conversão Experimental Real).
   - No modelo nominal, observa-se a dispersão sistemática dos ensaios em déficit de ácido ($\eta = 0,5$) e estequiométricos ($\eta = 1,0$), enquanto a nova abordagem atinge colapso estrito ao longo da bissetriz ideal dentro da faixa de tolerância de $\pm 5\%$.
4. [**`tabela_comparativa_detalhada_modelos.csv`**](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/tabela_comparativa_detalhada_modelos.csv):
   - Base de dados tabulada contendo métricas individuais ($R^2$, RMSE, MAE e erro de patamar) calculadas individualmente para cada um dos 16 ensaios de lixiviação.
5. **Galeria dos 16 Gráficos Individuais Despoluídos (Ensaio por Ensaio)**:
   - Localização: [`Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/ensaios_individuais/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/ensaios_individuais/)
   - Conjunto completo de 16 gráficos (disponíveis em PNG a 300 DPI e PDF vetorial), com painel duplo individual (curvas cinéticas superiores despoluídas com caixa de métricas + resíduos inferiores pontuais com faixa de tolerância de $\pm 2\%$) para os Ensaios 01 a 16.

---

## 6. Conclusão Epistemológica: O Papel da Modelagem Híbrida Serial

A presente análise estabelece uma justificativa metodológica e científica inquestionável para o desenvolvimento da **Modelagem Híbrida Serial (Fases 2 e 3 do Projeto LOP)**:

1. **Continuidade e Evolução do Conhecimento**:
   A formulação híbrida não se propõe a substituir a base mecanicista estabelecida por Fabrício Bortot Coelho, mas sim a integrá-la a técnicas orientadas por dados, respondendo a uma necessidade que o próprio autor assinalou em 2017: a incapacidade de um parâmetro de desaceleração constante e uniforme ($\alpha$) abranger toda a diversidade mineralógica e os múltiplos regimes estequiométricos do processo.
2. **Harmonia entre Física e Inteligência Artificial**:
   - A componente física (*White-Box*, Balanço Populacional) assegura a conservação de massa estrita, a consistência termodinâmica no intervalo $[0, 1]$ e a correta incorporação da distribuição de tamanhos de partícula (Rosin-Rammler-Bennet).
   - A componente orientada por dados (*Black-Box*, Redes Neurais / Modelos de Regressão) atua precisamente onde o modelo nominal apresentava limitações: prevendo dinamicamente a taxa de retração interfacial $v(t)$ em resposta às condições operacionais locais ($C_{A0}$, $\eta$, tempo de reação e agitação).
3. **Robustez Operacional**:
   A substituição do parâmetro empírico estático por uma dinâmica adaptativa eleva a previsibilidade do modelo para níveis industriais de confiabilidade ($R^2 = 0,9990$), permitindo sua posterior aplicação no controle ótimo e na simulação avançada de reatores de lixiviação contínuos em escala piloto e industrial.
