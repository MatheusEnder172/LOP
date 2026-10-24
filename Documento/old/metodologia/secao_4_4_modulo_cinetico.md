## 4.4. Metodologia Cinética de Retração Interfacial e Balanço Estequiométrico

Nesta subseção são estabelecidos os fundamentos cinéticos heterogêneos que governam a velocidade linear de dissolução das partículas de zincita, a dedução matemática da taxa de retração diametral interfacial, a incorporação do termo de amortecimento empírico e a dedução analítica dos limites assintóticos de conversão e esgotamento de ácido. O foco desta etapa é estritamente metodológico, detalhando como as leis constitutivas e os balanços estequiométricos foram formulados e acoplados para alimentar o resolvedor do Balanço Populacional e os modelos híbridos. A discussão e a análise quantitativa dos perfis temporais simulados frente aos dados experimentais são apresentadas na Seção 5 (Resultados e Discussão).

---

### 4.4.1. Mecanismo Cinético Heterogêneo: Modelo do Núcleo em Diminuição (SCM)

A lixiviação ácida de concentrados ustulados de zinco envolve a reação química de dissolução heterogênea do óxido de zinco livre (zincita) pelo ácido sulfúrico em meio aquoso, representada estequiometricamente pela reação global irreversível:

$$\text{ZnO (s)} + \text{H}_2\text{SO}_4\text{ (aq)} \rightarrow \text{ZnSO}_4\text{ (aq)} + \text{H}_2\text{O (l)}$$

Na literatura hidrometalúrgica de processos heterogêneos de dissolução mineral particulada (Levenspiel, 1999; Szekely; Evans; Sohn, 1976), o avanço reacional de partículas densas sem formação de camada porosa de cinzas insolúveis é classicamente descrito pelo Modelo do Núcleo em Diminuição (*Shrinking Core Model* — SCM) ou Modelo da Partícula Reagente de Tamanho Decrescente (*Shrinking Particle Model*). Conforme demonstrado experimentalmente por Balarini (2009) para a calcina de zinco, a velocidade global de extração em regime de intensa agitação mecânica (1000 rpm) é integralmente controlada pela etapa química de reação na superfície externa das partículas sólidas, sendo a resistência à difusão mássica externa no filme líquido interfacial perfeitamente desprezível.

Considerando partículas sólidas com geometria aproximadamente esférica de diâmetro característico $D$, o balanço molar diferencial de consumo de zincita pura na interface reacional sólido-líquido é formalizado pela Equação (4.14):

$$- \frac{dn_B}{dt} = - \frac{d}{dt} \left( \rho_s \cdot \frac{\pi D^3}{6} \right) = - \frac{\rho_s \pi D^2}{2} \cdot \frac{dD}{dt} = \pi D^2 \cdot r_s \tag{4.14}$$

sendo:
- $n_B$: quantidade de matéria de zincita na partícula (mol);
- $\rho_s$: densidade molar da zincita sólida pura ($\rho_s = 69,2\ \text{mol}\cdot\text{L}^{-1}$ ou $6,92 \times 10^{-2}\ \text{mol}\cdot\text{cm}^{-3}$);
- $D$: diâmetro instantâneo da partícula de sólido ($\mu\text{m}$);
- $r_s$: taxa intrínseca de reação química superficial por unidade de área interfacial ($\text{mol}\cdot\mu\text{m}^{-2}\cdot\text{min}^{-1}$).

Isolando a derivada temporal do diâmetro $D$ na Equação (4.14), obtém-se a velocidade linear de retração interfacial clássica do Modelo de Núcleo em Diminuição (Balarini, 2009), expressa pela Equação (4.15):

$$\left( \frac{dD}{dt} \right)_0 = - \frac{2}{\rho_s} \cdot k_s \cdot C_{Af}(t) \tag{4.15}$$

sendo $k_s$ a constante cinética intrínseca superficial de reação ($k_s = 1,8 \times 10^4\ \mu\text{m}\cdot\text{min}^{-1}$, determinada por Balarini, 2009, p. 115) e $C_{Af}(t)$ a concentração instantânea de ácido sulfúrico livre em solução ($\text{mol}\cdot\text{L}^{-1}$). O sinal negativo evidencia a natureza de encolhimento físico da partícula sólida.

---

### 4.4.2. Formulação da Taxa de Retração com Termo de Amortecimento (Bortot Coelho, 2017)

A formulação cinética clássica da Equação (4.15) assume que a taxa de dissolução interfacial é exclusivamente proporcional à concentração de ácido livre remanescente. No entanto, ensaios experimentais em reatores batelada e contínuos revelam que a reação real sofre uma severa desaceleração cinética nas etapas intermediárias e tardias ($t > 1\text{ min}$), muito superior àquela explicada unicamente pelo consumo termodinâmico de reagente líquido. Esse fenômeno decorre de fatores combinados característicos do sistema industrial: efeito do íon comum decorrente do acúmulo de cátions $\text{Zn}^{2+}$ em solução, aumento da força iônica do licor, passivação localizada e competição difusiva superficial (Balarini, 2009; Bortot Coelho, 2017).

Para capturar esse efeito de retardamento na modelagem mecanicista sem recorrer a correções termodinâmicas empíricas complexas de coeficientes de atividade, Bortot Coelho (2017, Capítulo 4 e Capítulo 5, p. 155) formulou uma extensão fenomenológica para a taxa de retração interfacial. Introduziu-se um termo antagônico de amortecimento proporcional à quantidade acumulada de ácido já consumida na reação ($\Delta C_A = C_{A0} - C_{Af}(t)$), resultando na Equação (4.16):

$$v(t) = \frac{dD}{dt} = - \frac{2}{\rho_s} \left[ k_s \cdot C_{Af}(t) - \alpha \cdot (C_{A0} - C_{Af}(t)) \right] \tag{4.16}$$

sendo:
- $v(t) = dD/dt$: taxa linear instantânea de variação diametral ($\mu\text{m}\cdot\text{min}^{-1}$);
- $C_{A0}$: concentração molar inicial de ácido sulfúrico adicionada na carga ($\text{mol}\cdot\text{L}^{-1}$);
- $C_{Af}(t)$: concentração molar instantânea de ácido sulfúrico livre remanescente no licor ($\text{mol}\cdot\text{L}^{-1}$);
- $\alpha$: parâmetro cinético de retardamento ou amortecimento empírico ($\alpha_{\text{nominal}} = 5,5 \times 10^3\ \mu\text{m}\cdot\text{min}^{-1}$, obtido por calibração estática em Bortot Coelho, 2017, Tabela 5.9).

A partir da Equação (4.16), define-se a força motriz líquida reacional de dissolução superficial interfacial $F_{\text{motriz}}(t)$, expressa pela Equação (4.17):

$$F_{\text{motriz}}(t) = k_s \cdot C_{Af}(t) - \alpha \cdot (C_{A0} - C_{Af}(t)) = (k_s + \alpha) \cdot C_{Af}(t) - \alpha \cdot C_{A0} \tag{4.17}$$

A velocidade linear de retração expressa na Equação (4.16) exibe uma propriedade metodológica de extrema relevância para a resolução do Balanço Populacional: a taxa $v(t)$ é **espacialmente uniforme**, ou seja, independe do diâmetro instantâneo $D$ da partícula, dependendo exclusivamente do estado químico do meio reacional ($C_{Af}$ e $C_{A0}$). Isso implica que todas as classes granulométricas presentes na polpa encolhem exatamente com a mesma velocidade linear instantânea $v(t)$ em um determinado tempo $t$, simplificando analiticamente a integração numérica do PBM.

---

### 4.4.3. Dedução da Acidez Crítica de Parada e Limite Assintótico de Conversão

A formulação cinética modificada pela Equação (4.16) conduz a uma consequência matemática e termodinâmica fundamental: a existência de um limiar mínimo de acidez residual no qual a taxa de retração se anula antes mesmo do esgotamento total do reagente ácido.

A dissolução interfacial cessa quando a força motriz líquida se iguala a zero ($F_{\text{motriz}} = 0 \Leftrightarrow v = 0$). Igualando-se a Equação (4.17) a zero:

$$(k_s + \alpha) \cdot C_{Af}^* - \alpha \cdot C_{A0} = 0$$

Isolando-se a concentração crítica de ácido livre de interrupção reacional ($C_{Af}^*$), deduz-se analiticamente a Equação (4.18):

$$C_{Af}^* = C_{A0} \cdot \left( \frac{\alpha}{k_s + \alpha} \right) \tag{4.18}$$

Substituindo-se a relação de conservação de massa em batelada de Herbst (1979) — Equação (4.6), $C_{Af}(t) = C_{A0}[1 - X_{\text{Zn}}(t)/\eta]$ — na condição de parada da Equação (4.18), obtém-se:

$$C_{A0} \cdot \left[ 1 - \frac{X_{\text{Zn}}^{\text{Max}}}{\eta} \right] = C_{A0} \cdot \left( \frac{\alpha}{k_s + \alpha} \right)$$

Cancelando-se $C_{A0}$ em ambos os membros e rearranjando algebricamente a expressão para isolar a conversão fracionária, deduz-se o patamar assintótico teórico máximo de conversão de zincita ($X_{\text{Zn}}^{\text{Max}}$) alcançável pelo modelo cinético mecanicista, formalizado pela Equação (4.19):

$$X_{\text{Zn}}^{\text{Max}} = \eta \cdot \left( 1 - \frac{\alpha}{k_s + \alpha} \right) = \eta \cdot \left( \frac{k_s}{k_s + \alpha} \right) \tag{4.19}$$

com a imposição da restrição física superior de conservação de massa $X_{\text{Zn}}^{\text{Max}} \le 1,0$.

A Equação (4.19) possui um significado metodológico basilar para o projeto:
1. Para o modelo cinético puramente mecanicista com parâmetros nominais da literatura ($k_s = 18000\ \mu\text{m/min}$ e $\alpha = 5500\ \mu\text{m/min}$), a fração reacional máxima é modulada pelo fator constante:
   $$\frac{k_s}{k_s + \alpha} = \frac{18000}{18000 + 5500} \approx 0,7660$$
2. Esse resultado demonstra algebricamente que, mesmo sob proporção equimolar estequiométrica ($\eta = 1,0$), o modelo cinético com amortecimento estático prevê um teto de conversão assintótico de aproximadamente $76,6\%$, em vez dos $85\%$ a $87\%$ observados experimentalmente na bancada;
3. Essa discrepância sistemática entre a formulação mecanicista de parâmetros constantes e o comportamento empírico real justifica metodologicamente a necessidade de acoplamento com modelos de aprendizado de máquina (modelagem híbrida), nos quais o parâmetro $\alpha$ ou o fator de atenuação é ajustado dinamicamente em função das variáveis operacionais do processo.

---

### 4.4.4. Projeção Física de Não-Crescimento e Acoplamento Estequiométrico

Tendo em vista que a dissolução química de óxido de zinco em ácido sulfúrico aquoso a 40 °C é um processo termodinamicamente irreversível, as partículas minerais sólidas não podem sofrer precipitação ou regeneração volumétrica reversa caso a concentração de ácido decaia abaixo do limite crítico ($C_{Af} < C_{Af}^*$). 

Para impedir violações físicas e garantir a estabilidade das rotinas numéricas, a taxa de retração interfacial é submetida a um operador de projeção física unilateral de não-crescimento (*hard physical constraint*), formalizado pela Equação (4.20):

$$v(t) = \min\left( 0,\ \frac{dD}{dt} \right) \tag{4.20}$$

Dessa forma, caso a força motriz líquida da Equação (4.17) resulte em valor negativo ($F_{\text{motriz}} < 0$), o algoritmo trunca instantaneamente a velocidade para $v(t) = 0$, congelando a distribuição granulométrica no instante de esgotamento.

O acoplamento computacional do módulo cinético segue o seguinte fluxo analítico de execução:
1. Em cada passo temporal da simulação, a conversão global acumulada $X_{\text{Zn}}(t)$ é fornecida pelo integrador do Balanço Populacional;
2. A concentração instantânea de ácido livre residual $C_{Af}(t)$ é imediatamente atualizada pela relação analítica de Herbst (1979) (Equação 4.6);
3. A força motriz líquida e a taxa de retração $v(t)$ são calculadas pelas Equações (4.16) e (4.20), fornecendo a velocidade de deslocamento de malha para a evolução temporal dos diâmetros de partículas.

---

### 4.4.5. Síntese dos Parâmetros Físico-Químicos e Cinéticos Nominais

Os parâmetros constitutivos, cinéticos e estequiométricos que compõem o módulo de lixiviação ácida de bancada encontram-se sintetizados na Tabela 4.3, discriminados por suas respectivas fontes acadêmicas primárias de determinação.

**Tabela 4.3 – Parâmetros físico-químicos, termodinâmicos e cinéticos nominais do sistema de lixiviação de calcina de zinco.**

| Parâmetro / Propriedade | Símbolo | Valor Nominal | Unidade | Significado Físico / Fonte Primária |
| :--- | :---: | :---: | :---: | :--- |
| Constante cinética superficial | $k_s$ | $1,8 \times 10^4$ | $\mu\text{m}\cdot\text{min}^{-1}$ | Constante de velocidade de reação química superficial / Balarini (2009, p. 115) |
| Parâmetro empírico de amortecimento | $\alpha$ | $5,5 \times 10^3$ | $\mu\text{m}\cdot\text{min}^{-1}$ | Retardamento cinético por acúmulo de íons e não-idealidade / Bortot Coelho (2017, Tabela 5.9) |
| Densidade molar da zincita pura | $\rho_s$ | 69,2 | $\text{mol}\cdot\text{L}^{-1}$ | Concentração molar de ZnO na fase sólida cristalina / Picnometria a 25 °C |
| Massa molar da zincita | $MM_{\text{ZnO}}$ | 81,38 | $\text{g}\cdot\text{mol}^{-1}$ | Estequiometria do óxido de zinco puro |
| Massa molar do zinco elementar | $MM_{\text{Zn}}$ | 65,38 | $\text{g}\cdot\text{mol}^{-1}$ | Estequiometria do elemento de interesse hidrometalúrgico |
| Massa molar do ferro elementar | $MM_{\text{Fe}}$ | 55,85 | $\text{g}\cdot\text{mol}^{-1}$ | Estequiometria de correção de dissolução da ferrita de zinco |
| Fração de zincita na calcina (química) | $T_{\text{ZnO}}$ | 0,761 (76,1%) | - | Teor mássico de óxido livre via digestão amoniacal / Elgersma et al. (1992) |
| Fração operacional de cálculo de carga | $T_{\text{ZnO},\text{op}}$ | 0,8138 | - | Base de cálculo da carga de bancada (1 mol ZnO / 100 g sólido) / Bortot Coelho (2017) |
| Volume reacional da fase líquida | $V$ | 0,400 (400 mL) | $\text{L}$ | Volume de solução sulfúrica no reator encamisado de bancada |
| Fator estequiométrico assintótico nominal | $\frac{k_s}{k_s + \alpha}$ | 0,7660 | - | Limite fracionário intrínseco de conversão mecanicista (Eq. 4.19) |

*Fonte: Elaborado pelos autores a partir de dados de Balarini (2009) e Bortot Coelho (2017).*
