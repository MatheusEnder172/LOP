# Análise Granulométrica e Validação do Modelo RRB: Etapa 0.2

**Arquivo analisado**: [`Base de dados/raw/granulometria_RRB.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Base%20de%20dados/raw/granulometria_RRB.csv)  
**Fontes bibliográficas de referência**:
- Dissertação de Mestrado: Fabrício Eduardo Bortot Coelho (PPGEM/UFMG, 2017), Capítulo 5 (Seção 5.1.2, Tabelas 5.4, 5.5, 5.6 e Figuras 5.2, 5.3 e 5.4).
- Modelagem de processos particulados: Randolph & Larson (1988) — *Theory of Particulate Processes*.
- LeBlanc & Fogler (1987) — *Population balance modeling of the dissolution of polydisperse solids*.
- Dicionário de rastreabilidade: [`Base de dados/RASTREABILIDADE_DADOS.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Base%20de%20dados/RASTREABILIDADE_DADOS.md).

**Gráficos gerados nesta etapa**:
- Imagem de alta resolução (300 DPI): [`Código/outputs/etapa_0_2/fig_02_granulometria_RRB.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_0_2/fig_02_granulometria_RRB.png)
- Arquivo vetorial para relatórios/impressão: [`Código/outputs/etapa_0_2/fig_02_granulometria_RRB.pdf`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_0_2/fig_02_granulometria_RRB.pdf)

---

## 1. Fundamentação e Métodos Experimentais de Medição

A distribuição de tamanhos das partículas do concentrado ustulado de zinco (calcina da Nexa Resources - Três Marias) foi determinada por duas técnicas complementares devido à ampla faixa de diâmetros:
1. **Peneiramento a Úmido**: Aplicado para as frações mais grosseiras (peneiras Tyler de aberturas entre $38\,\mu\text{m}$ e $297\,\mu\text{m}$ / malhas #400 a #50).
2. **Difração a Laser**: Utilizada no equipamento Sympatec Helos 12LA para caracterizar com exatidão as partículas ultrafinas passantes na malha de $74\,\mu\text{m}$ (faixa de $0,45\,\mu\text{m}$ a $74,0\,\mu\text{m}$).

No ponto de sobreposição ($74\,\mu\text{m}$ / malha #200), ambas as técnicas registraram exatamente **$84,4\%$ de fração passante acumulada**, comprovando a perfeita concordância entre os dois métodos.

---

## 2. Equacionamento Matemático de Rosin-Rammler-Bennet (RRB)

### 2.1. Função Distribuição Mássica Acumulada Passante $F(D)$
A fração mássica de partículas com diâmetro menor ou igual a $D$ é descrita por:

$$F(D) = 1 - \exp\left[ -\left(\frac{D}{D_{63,2}}\right)^m \right]$$

Onde:
- **$D_{63,2} = 41,65\,\mu\text{m}$**: Diâmetro característico da amostra, correspondente à abertura na qual passam exatamente $1 - e^{-1} \approx 63,2\%$ do material em massa.
- **$m = 1,022$**: Módulo de dispersão ou uniformidade (adimensional). Valores de $m$ próximos de $1,0$ indicam forte assimetria e ampla dispersão granulométrica.

### 2.2. Função Densidade de Frequência Inicial $f_0(D)$
A derivada da fração acumulada fornece a densidade de distribuição contínua que atua como condição inicial obrigatória no Balanço Populacional:

$$f_0(D) = \frac{dF(D)}{dD} = \frac{m}{D_{63,2}} \left(\frac{D}{D_{63,2}}\right)^{m-1} \exp\left[ -\left(\frac{D}{D_{63,2}}\right)^m \right]$$

### 2.3. Linearização Clássica do Modelo RRB
A linearização da equação acumulada é obtida aplicando-se o logaritmo duplo:

$$\ln\left[ \ln\left( \frac{1}{1 - F(D)} \right) \right] = m \ln(D) - m \ln(D_{63,2})$$

Plotando-se $y = \ln[\ln(1/(1-F))]$ contra $x = \ln(D)$, a inclinação fornece o expoente $m$ e o coeficiente linear fornece $-m \ln(D_{63,2})$.

---

## 3. Resultados Estatísticos e Validação do Ajuste

A avaliação quantitativa do ajuste do modelo RRB aos dados experimentais revelou:

| Métrica Estatística | Valor Obtido | Critério de Aceitação | Avaliação |
| :--- | :---: | :---: | :---: |
| **Coeficiente de Determinação ($R^2$) Global** | **$0,9962$** | $> 0,9900$ | Excelente aderência |
| **Raiz do Erro Quadrático Médio (RMSE)** | **$0,0210$** ($2,1\%$) | $< 0,0500$ | Erro residual mínimo |
| **Erro Absoluto Médio (MAE)** | **$0,0142$** ($1,4\%$) | $< 0,0300$ | Dispersão uniforme |
| **$R^2$ da Regressão Linearizada** | **$0,9908$** | $> 0,9800$ | Confirma modelo RRB |

---

## 4. Análise dos Quatro Painéis da Figura

- **Painel (a) — Escala Linear**: Demonstra que o concentrado atinge $99,5\%$ de passante em $297\,\mu\text{m}$, mas mais de $60\%$ do material é menor que $40\,\mu\text{m}$. A linha tracejada em $D = 41,65\,\mu\text{m}$ intercepta com precisão o patamar de $63,2\%$.
- **Painel (b) — Escala Semi-Logarítmica**: Evidencia o formato sigmoidal característico em escala logarítmica (idêntico à Figura 5.4 da dissertação de Bortot Coelho), demonstrando que o modelo RRB reproduz perfeitamente tanto a cauda de partículas ultrafinas ($< 2\,\mu\text{m}$) quanto os grãos grosseiros ($> 150\,\mu\text{m}$).
- **Painel (c) — Função Densidade $f_0(D)$**: Revela que a maior densidade numérica e mássica está concentrada em diâmetros inferiores a $30\,\mu\text{m}$. O diâmetro médio da população é $\bar{\mu} = 41,28\,\mu\text{m}$, com coeficiente de variação $\text{CV} = 0,97$.
- **Painel (d) — Linearização RRB**: A regressão linear dos dados transformados resultou em $y = 1,0223x - 3,8468$ com $R^2 = 0,9908$, reproduzindo fielmente os parâmetros reportados na Tabela 5.6 da dissertação ($m \approx 1,022$ e $D_{63,2} \approx 41,65\,\mu\text{m}$).

---

## 5. Conexão Direta com a Modelagem de Balanço Populacional (Fase 1)

1. **Condição Inicial do Resolvedor PBM**:
   A função $f_0(D)$ calculada aqui será utilizada na **Etapa 1.1** para compor a malha de $N = 1000$ pontos entre $D_{\min} = 0,01\,\mu\text{m}$ e $D_{\max} = 297\,\mu\text{m}$.
2. **Cálculo do Terceiro Momento Volumétrico**:
   O volume total inicial de sólidos $M_3(0)$ será avaliado pela integração numérica do terceiro momento:
   $$M_3(0) = \int_0^{D_{\max}} D^3 f_0(D) dD$$
   Esse valor serve como denominador para calcular a fração convertida $X_{\text{Zn}}(t) = 1 - M_3(t)/M_3(0)$.
3. **Explicação da Cinética Inicial Ultra-Rápida**:
   A confirmação de que cerca de $60\%$ da massa está abaixo de $38\,\mu\text{m}$ (e $30\%$ abaixo de $15\,\mu\text{m}$) explica por que mais de $80\%$ da reação se completa nos primeiros 30 segundos observados na Etapa 0.1: as partículas ultrafinas têm área específica volumétrica elevadíssima e desaparecem quase instantaneamente.
