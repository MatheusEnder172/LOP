# RASTREABILIDADE E PROVENIÊNCIA DOS DADOS EXPERIMENTAIS

Este documento detalha a origem exata de cada arquivo de dados presente na pasta `Base de dados/raw/`, indicando o documento fonte, capítulo, página, tabela original e condições experimentais.

---

## 1. Documento Fonte Principal
* **Título**: *Desenvolvimento e Validação de um Modelo de Balanço Populacional para a Lixiviação de um Concentrado Ustulado de Zinco em Bancada e em Escala Piloto*
* **Autor**: Fabrício Eduardo Bortot Coelho (Orientador do LOP)
* **Grau / Instituição**: Dissertação de Mestrado, PPGEM - Escola de Engenharia, Universidade Federal de Minas Gerais (UFMG), Outubro/2017.
* **Arquivo Local**: `Artigos/Lixiviação de um Concentrado Ustulado de Zinco em Bancada e em Escala Piloto.pdf`

---

## 2. Rastreabilidade Arquivo por Arquivo

### 2.1. `bancada_batelada_A1_1.csv`
* **Local no PDF**: **Apêndice A1.1, Tabela A1.1** (Página 200 do documento / Página 227 do arquivo PDF).
* **Título Original**: *"TABELA A1.1 – Média dos resultados obtidos ensaios de lixiviação descontínuos em bancada, realizados em triplicata."*
* **Condições Experimentais Fixas**:
  * Volume de solução lixiviante: $V = 400\,\text{mL} = 0,4\,\text{L}$
  * Temperatura: $T = 40^\circ\text{C}$
  * Rotação do agitador mecânico: $1000\,\text{rpm}$
  * Concentrado mineral: Calcina da Nexa Resources (Três Marias - MG)
* **Colunas e Significado**:
  * `ensaio`: Identificador do ensaio em bancada (1 a 16).
  * `razao_molar_eta`: Razão molar estequiométrica $\eta = \frac{n_{A0}}{n_{B0}} = \frac{V \cdot C_{A0}}{m_{B0} T_{\text{ZnO}} / MM_{\text{ZnO}}}$ (valores: 0.5, 1.0, 1.5, 3.1).
  * `CA0_mol_L`: Concentração inicial de $\text{H}_2\text{SO}_4$ ($0,10; 0,50; 1,00; 1,50\,\text{mol/L}$).
  * `razao_solido_liquido_g_L`: Razão mássica sólido/líquido ($3,0$ a $300,0\,\text{g/L}$).
  * `mB0_g`: Massa de concentrado ustulado adicionada ao reator ($1,3$ a $120,0\,\text{g}$).
  * `CAf_mol_L`: Concentração residual de $\text{H}_2\text{SO}_4$ livre no licor ao final do ensaio ($t = 15\,\text{min}$).
  * `pH0`: pH inicial medido do licor.
  * `pHf`: pH final medido do licor.
  * `Zn_licor_g_L`: Concentração mássica total de $\text{Zn}$ em solução ao final do ensaio ($\text{g/L}$).
  * `XZn`: Conversão fracionária da zincita ao final do ensaio ($0$ a $1$).
  * `XFe`: Extração fracionária de ferro da matriz sólida ($0$ a $0,10$).

---

### 2.2. `cinetica_batelada_A1_4.csv`
* **Local no PDF**: **Apêndice A1.1, Tabela A1.4** (Página 201 do documento / Página 228 do arquivo PDF).
* **Título Original**: *"TABELA A1.4 – Média da conversão de zinco em função do tempo ($X_{\text{Zn}}$) obtidas nas três réplicas dos ensaios de lixiviação descontínuos em bancada."*
* **Condições Experimentais**: $V = 400\,\text{mL}$, $T = 40^\circ\text{C}$, $1000\,\text{rpm}$.
* **Como os dados foram estruturados**:
  * Na tabela original do PDF, os tempos ($0; 0,5; 1; 2; 3; 4; 5; 15\,\text{min}$) estavam em colunas horizontais.
  * No arquivo CSV gerado, os dados foram transformados para o formato longo (*tidy/long format*), com as colunas: `ensaio`, `razao_molar_eta`, `CA0_mol_L`, `t_min`, `XZn`.
  * Essa estrutura permite indexação temporal direta por ensaio, facilitando a plotagem das curvas cinéticas $X_{\text{Zn}}$ vs. $t$ e a calibração de modelos dinâmicos.

---

### 2.3. `piloto_continuo_A1_6.csv`
* **Local no PDF**: **Apêndice A1.2, Tabela A1.6** (Página 202 do documento / Página 229 do arquivo PDF).
* **Título Original**: *"TABELA A1.6 – Resultados do ensaio de lixiviação contínuo na planta piloto com vazão volumétrica de alimentação de $0,41\,\text{L}\cdot\text{min}^{-1}$."*
* **Condições Operacionais da Planta Piloto**:
  * Configuração: 3 reatores CSTR em série de $6\,\text{L}$ cada (Volume total $18\,\text{L}$).
  * Vazão de alimentação líquida: $V_0 = 0,41\,\text{L/min}$.
  * Tempo de residência teórico por reator: $\tau = 6,0 / 0,41 \approx 14,6\,\text{min}$.
  * Concentração inicial de ácido: $C_{A0} = 0,5\,\text{mol/L}$.
  * Razão molar: $\eta = 1,0$.
  * Temperatura: $T = 40^\circ\text{C}$.
  * Agitação mecânica: $500\,\text{rpm}$.
* **Variáveis no Tempo ($t = 45$ a $150\,\text{min}$)**:
  * Conversão de zinco em cada reator: `XZn_R1`, `XZn_R2`, `XZn_R3`.
  * Acidez livre residual em cada reator: `CAf_R1_mol_L`, `CAf_R2_mol_L`, `CAf_R3_mol_L`.
  * Extração de ferro em cada reator: `XFe_R1`, `XFe_R2`, `XFe_R3`.

---

### 2.4. `piloto_continuo_A1_7.csv`
* **Local no PDF**: **Apêndice A1.2, Tabela A1.7** (Página 202 do documento / Página 229 do arquivo PDF).
* **Título Original**: *"TABELA A1.7 – Resultados do ensaio de lixiviação contínuo na planta piloto com vazão volumétrica de alimentação de $0,21\,\text{L}\cdot\text{min}^{-1}$."*
* **Condições Operacionais**:
  * Cascata de 3 CSTRs ($V = 6\,\text{L}$ cada).
  * Vazão de alimentação: $V_0 = 0,21\,\text{L/min}$.
  * Tempo de residência teórico por reator: $\tau = 6,0 / 0,21 \approx 28,6\,\text{min}$.
  * Mesmas condições químicas: $C_{A0} = 0,5\,\text{mol/L}$, $\eta = 1,0$, $T = 40^\circ\text{C}$, $500\,\text{rpm}$.
* **Variáveis no Tempo ($t = 90$ a $300\,\text{min}$)**:
  * Acompanhamento transiente até o estado estacionário para os 3 reatores da cascata.

---

### 2.5. `granulometria_RRB.csv`
* **Local no PDF**: **Capítulo 5 (Resultados e Discussão), Tabela 5.4** (Página 129 do documento / Página 156 do arquivo PDF).
* **Título Original**: *"TABELA 5.4 – Fração mássica acumulada de partículas do concentrado ustulado de zinco com diâmetro menor do que d#."*
* **Métodos Combinados**:
  * Peneiramento a úmido: 8 peneiras Tyler ($38$ a $297\,\mu\text{m}$).
  * Difração a Laser: Equipamento Helos 12LA da Sympatec para frações finas ($0,45$ a $74\,\mu\text{m}$).
* **Importância**: Base experimental que calibrou a função Rosin-Rammler-Bennet (RRB) com $R^2 > 0,99$ (Tabela 5.6 e Equação 5.2).

---

### 2.6. `parametros_fpm_nominal.json`
* **Local no PDF**: **Capítulo 5, Tabela 5.9** (Página 155 do documento / Página 182 do arquivo PDF) e **Tabela 5.1** (Página 125).
* **Parâmetros Físicos e Cinéticos Nominais**:
  * Constante cinética superficial: $k_s = 1,8 \times 10^4\,\mu\text{m/min}$ (Balarini, 2009).
  * Parâmetro estático de ajuste: $\alpha = 5,5 \times 10^3\,\mu\text{m/min}$ (Bortot Coelho, 2017).
  * Densidade molar da zincita: $\rho_s = 69,2\,\text{mol/L}$.
  * Massa molar do $\text{ZnO}$: $MM_{\text{ZnO}} = 81,38\,\text{g/mol}$.
  * Teor de $\text{ZnO}$ no concentrado: $76,1\%\ \text{m/m}$.
  * Parâmetros da distribuição RRB: $D_{63,2} = 41,65\,\mu\text{m}$, $m = 1,022$.
