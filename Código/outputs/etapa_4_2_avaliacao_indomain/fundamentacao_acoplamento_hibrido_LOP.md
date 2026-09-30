# Fundamentação Teórica e Formulação do Acoplamento Híbrido Serial (DDM → PBM)

**Projeto**: Modelagem Híbrida de Lixiviação de Concentrado de Zinco (LOP / DEQ / UFMG)  
**Documento Técnico**: Formulação Fenomenológica e Acoplamento Orientado por Dados  
**Data**: 2026-09-27  

---

## 1. Contextualização e Desafio da Modelagem Clássica

A lixiviação oxidativa/ácida de concentrados ustulados de zinco (compostos predominantemente por zincita ZnO e ferrita de zinco ZnFe₂O₄) em reatores industriais envolve a interação acoplada entre hidrodinâmica, transporte de massa difusivo em camada limite, dissolução interfacial controlada por reação superficial e passivação progressiva por precipitados secundários (sílica coloidal, jarositas e enxofre elementar).

### 1.1 O Modelo Clássico Puramente Fenomenológico (FPM Puro)
Na formulação pioneira de Herbst (1979) e adaptada por Bortot Coelho (2017), a dinâmica de encolhimento de populações polidispersas de partículas esféricas é descrita pela Equação do Balanço Populacional (PBM):

$$\frac{\partial f(D, t)}{\partial t} + \frac{\partial [v(D, t) \cdot f(D, t)]}{\partial D} = 0$$

Sob o postulado de que a taxa de retração interfacial $v(t) = dD/dt$ é homogênea (independente do diâmetro $D$), o Método das Características permite colapsar a EDP hiperbólica em uma equação ordinária unidimensional para o deslocamento diametral acumulado $\delta(t)$:

$$\frac{d\delta}{dt} = |v(t)| = -v(t) \ge 0, \quad \delta(0) = 0$$

Para relacionar a velocidade de dissolução $v(t)$ com as concentrações químicas no licor, os modelos puramente fenomenológicos utilizam equações empíricas do tipo:

$$|v(t)| = \frac{k_s \cdot C_{Af}(t) - \alpha \cdot [C_{A0} - C_{Af}(t)]}{\rho_s \cdot \text{fator}}$$

**A Fragilidade do FPM Puro**:
O parâmetro $\alpha$ (amortecimento cinético) é assumido como constante global ($\alpha = 3,43\ \mu\text{m/min}$). Entretanto, a lixiviação real exibe fenômenos superficiais altamente dinâmicos:
1. Formação de biofilmes/camadas passivantes de porosidade variável;
2. Efeito de força iônica decorrente da liberação de cátions Zn²⁺ e Fe³⁺ no meio;
3. Mudança contínua de regime cinético (transição de controle químico superficial puro para difusão combinada através da camada de cinzas).

Como consequência, o FPM Puro falha gravemente em regimes de baixa acidez inicial ($C_{A0} = 0,10\ \text{mol/L}$), onde superestima a resistência ao ataque químico e atinge $R^2$ medíocres entre 0,53 e 0,62.

---

## 2. A Ilusão do Modelo Puramente Baseado em Dados (DDM Puro)

Com o advento do aprendizado de máquina, uma alternativa tentadora é treinar um regressor supervisionado (Random Forest, Redes Neurais Profundas, XGBoost) para predizer diretamente a conversão $X_{\text{Zn}}(t)$ ou a taxa de retração $|v(t)|$.

### 2.1 A Quebra Termodinâmica em Malha Aberta
Em ensaios de excesso estequiométrico ($\eta \ge 1,5$), o modelo de Machine Learning ajusta perfeitamente os dados experimentais ($R^2 > 0,98$). Contudo, quando submetido a regimes limitantes de solvente ($\eta = 0,5$):
- O reagente ácido é integralmente consumido quando $X_{\text{Zn}}$ atinge 50% ($X_{\text{Zn}} = \eta = 0,50$);
- Como o modelo puramente orientado por dados não possui conexão intrínseca com o balanço de massa do solvente, ele continua prevendo $|v(t)| > 0$ devido à passagem do tempo $t$;
- O deslocamento acumulado $\delta(t)$ segue crescendo e a conversão prevista atinge patamares absurdos de 80% a 84%, gerando $R^2$ negativos ($-1,5$ a $-3,2$).

O DDM Puro, portanto, viola a Primeira Lei da Termodinâmica ao "criar reagente do nada" quando opera fora do domínio restrito em que foi calibrado.

---

## 3. A Arquitetura Híbrida Serial (DDM → PBM)

A modelagem híbrida serial proposta neste projeto combina o melhor dos dois mundos:
- **Componente Orientado por Dados (DDM)**: Atua exclusivamente no fenômeno de maior complexidade constitutiva (a taxa instantânea de retração interfacial $|v(t)|$), capturando as não-linearidades físico-químicas em função de $[T, C_{A0}, \eta, t]$;
- **Componente Mecanicista (PBM White-Box)**: Atua como guardião inegociável da conservação de massa e termodinâmica, aplicando a convolução granulométrica analítica e o balanço estequiométrico de Herbst.

```
Condições Operacionais
 [T, CA0, eta, t] 
        │
        ▼
┌────────────────────────────────────────┐
│      DDM Black-Box (Random Forest)     │  --> Prediz taxa interfacial não-linear
│       v(t) = f_DDM(T, CA0, eta, t)     │      |v(t)| >= 0  (µm/min)
└────────────────────────────────────────┘
        │
        ▼  [Malha Fina de Integração Sub-Segundo: delta(t) = ∫ |v| dt]
┌────────────────────────────────────────┐
│     PBM White-Box (Método Analítico)   │  --> Convolução granulométrica sobre
│ X_Zn(t) = 1 - 1/M3,0 ∫ (D-delta)³ f0 dD│      distribuição contínua RRB
└────────────────────────────────────────┘
        │
        ▼  [Garantia Termodinâmica: Balanço de Herbst]
┌────────────────────────────────────────┐
│      Projeção Física Estequiométrica   │  --> Se CAf = 0 (X_Zn >= eta), trava o
│  X_Zn <= min(1, eta) e CAf >= 0 mol/L  │      avanço químico e impõe v = 0
└────────────────────────────────────────┘
        │
        ▼
   Predições Finais
   [X_Zn(t), CAf(t)]
```

---

## 4. Formulação Matemática das Restrições e Convolução

### 4.1 Convolução Granulométrica sobre Rosin-Rammler-Bennett (RRB)
A distribuição mássica acumulada passante da calcina de zinco é descrita por:

$$W(D) = 1 - \exp\left[ -\left(\frac{D}{D'}\right)^m \right], \quad D' = 42,97\ \mu\text{m}, \quad m = 1,189$$

A função densidade volumétrica correspondente é dada por:

$$f_0(D) = \frac{m}{D'} \left(\frac{D}{D'}\right)^{m-1} \exp\left[ -\left(\frac{D}{D'}\right)^m \right]$$

Para cada instante de tempo $t$, o recuo uniforme $\delta(t)$ remove uma camada superficial de espessura $\delta/2$ de todas as partículas. As frações menores que $\delta(t)$ são integralmente dissolvidas. A conversão mássica $X_{\text{Zn}}(t)$ resulta da razão entre o volume de sólidos remanescente e o volume inicial:

$$X_{\text{Zn, PBM}}(t) = 1 - \frac{1}{M_{3,0}} \int_{\delta(t)}^{D_{\max}} (D - \delta(t))^3 \cdot f_0(D)\, dD$$

Onde $M_{3,0} = \int_0^{D_{\max}} D^3 f_0(D) dD$ é o terceiro momento volumétrico inicial.

### 4.2 Balanço de Massa do Ácido Sulfúrico (Herbst, 1979)
O consumo de ácido sulfúrico em sistema batelada relaciona-se estequiometricamente com o avanço da dissolução:

$$C_{Af}(t) = C_{A0} \cdot \left[ 1 - \frac{X_{\text{Zn}}(t)}{\eta} \right]$$

Onde a razão molar estequiométrica $\eta$ é definida operacionalmente por:

$$\eta = \frac{n_{\text{ácido, 0}}}{n_{\text{zincita, 0}}} = \frac{100 \cdot V_{\text{liq}} \cdot C_{A0}}{m_{B0}}$$

### 4.3 Truncamento Físico de Esgotamento
Como a concentração de reagente não pode assumir valores negativos ($C_{Af} \ge 0$), a máxima conversão quimicamente admissível em batelada é:

$$X_{\text{Zn}}^{\max} = \min(1,0;\ \eta)$$

No modelo híbrido serial, caso a convolução PBM alcance $X_{\text{Zn}} = X_{\text{Zn}}^{\max}$, o sistema impõe formalmente:

$$\left. \frac{dX_{\text{Zn}}}{dt} \right|_{t > t_{\text{esgotamento}}} = 0, \quad \left. |v(t)| \right|_{t > t_{\text{esgotamento}}} = 0$$

Isso assegura que o modelo híbrido serial nunca viole o balanço de massa, mesmo sob predições atípicas do módulo Black-Box.

---

## 5. Conclusões da Avaliação In-Domain

1. **Acurácia Sem Precedentes**: O Híbrido Serial alcançou $R^2 = 0,9737$ e $\text{RMSE} = 0,0526$ no conjunto completo dos 16 ensaios (128 pontos), reduzindo o erro residual em quase **48%** em relação ao modelo FPM Puro de referência ($\text{RMSE} = 0,1010$).
2. **Generalização em Teste Cego**: Nos 3 ensaios mantidos intocados durante a calibração cinético-estatística (Ensaios 8, 14 e 7), o modelo híbrido alcançou $R^2 = 0,9880$ e $\text{RMSE} = 0,0341$, demonstrando alta capacidade preditiva em condições operacionais distintas.
3. **Consistência Termodinâmica**: Em todos os 16 ensaios, $0 \le X_{\text{Zn}} \le 1$ e $C_{Af} \ge 0$ foram respeitados com 100% de rigor.
