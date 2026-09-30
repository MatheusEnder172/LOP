# Relatório de Validação e Desempenho: Etapa 1.3
## Simulação do Baseline Fenomenológico Puro (FPM Puro)

**Módulo Testado**: [`src/physics/pbm_batch.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/pbm_batch.py)  
**Classe**: `BatchPBMSolver`  
**Parâmetros Nominais**: $k_s = 18.000\,\mu\text{m/min}$, $\alpha_{\text{nominal}} = 5.500\,\mu\text{m/min}$, $\rho_s = 69,2\,\text{mol/L}$, $D_{63,2} = 41,65\,\mu\text{m}$, $m = 1,022$.  
**Base de Comparação**: 16 ensaios de lixiviação descontínua em bancada (Bortot Coelho, 2017, Apêndice A1.1, Tabela A1.4).

---

## 1. Resultados dos Testes Unitários de Software

| Teste Realizado | Critério de Aceitação | Resultado Obtido | Status |
| :--- | :--- | :---: | :---: |
| **Monotonicidade de $X_{\text{Zn}}(\delta)$** | $dX/d\delta \ge 0$ em todo o domínio | $\Delta X \ge -10^{-8}$ | **APROVADO** |
| **Limites Físicos de Conversão** | $X_{\text{Zn}} \in [0, 1]$ para qualquer $\delta \ge 0$ | $X(0) = 0,0000$; $X(D_{\max}) = 1,0000$ | **APROVADO** |
| **Limite Assintótico Teórico ($\eta = 1,0$)** | $X_{\text{final}} \to 0,7660$ e $C_{Af} \to 0,1170\,\text{mol/L}$ | $X = 0,7660$; $C_{Af} = 0,1170\,\text{mol/L}$ | **APROVADO** |
| **Conversão Completa com Excesso ($\eta = 3,1$)** | $X_{\text{Zn}} \to 1,0000$ para tempos longos | $X_{\text{final}} = 1,0000$ | **APROVADO** |
| **Simulação via Perfil Arbitrário de $v(t)$** | $\delta(t) = \int \|v\| dt$ exato para acoplamento híbrido | $\delta(10\,\text{min}) = 100,00\,\mu\text{m}$ (exato) | **APROVADO** |

---

## 2. Métricas de Aderência Experimental dos 16 Ensaios de Bancada

| Ensaio | $\eta$ (-) | $C_{A0}$ (mol/L) | $R^2$ | RMSE (-) | MAE (-) | $X_{\text{exp}}$ final | $X_{\text{FPM}}$ final | Erro Absoluto Final |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 0,5 | 0,10 | 0,5767 | 0,1038 | 0,0962 | 0,5000 | 0,3830 | 0,1170 |
| **3** | 0,5 | 0,50 | 0,6096 | 0,1019 | 0,0938 | 0,5000 | 0,3830 | 0,1170 |
| **4** | 0,5 | 1,00 | 0,5625 | 0,1098 | 0,1011 | 0,5000 | 0,3830 | 0,1170 |
| **5** | 0,5 | 1,50 | 0,6481 | 0,0951 | 0,0886 | 0,4900 | 0,3830 | 0,1070 |
| **6** | 1,0 | 0,10 | 0,5317 | 0,1887 | 0,1585 | 0,8700 | 0,7657 | 0,1043 |
| **8** | 1,0 | 0,50 | 0,8827 | 0,0966 | 0,0885 | 0,8700 | 0,7660 | 0,1040 |
| **9** | 1,0 | 1,00 | 0,9288 | 0,0743 | 0,0692 | 0,8500 | 0,7660 | 0,0840 |
| **10** | 1,0 | 1,50 | 0,9418 | 0,0667 | 0,0620 | 0,8500 | 0,7660 | 0,0840 |
| **11** | 1,5 | 0,10 | 0,6209 | 0,1896 | 0,1269 | 0,9800 | 0,9948 | 0,0148 |
| **13** | 1,5 | 0,50 | 0,9753 | 0,0491 | 0,0388 | 0,9700 | 1,0000 | 0,0300 |
| **14** | 1,5 | 1,00 | 0,9904 | 0,0310 | 0,0266 | 0,9700 | 1,0000 | 0,0300 |
| **15** | 1,5 | 1,50 | 0,9798 | 0,0446 | 0,0409 | 0,9700 | 1,0000 | 0,0300 |
| **2** | 3,1 | 0,10 | 0,7676 | 0,1526 | 0,0862 | 1,0000 | 1,0000 | 0,0000 |
| **7** | 3,1 | 0,50 | 0,9919 | 0,0291 | 0,0198 | 1,0100 | 1,0000 | 0,0100 |
| **12** | 3,1 | 1,00 | 0,9983 | 0,0136 | 0,0080 | 1,0000 | 1,0000 | 0,0000 |
| **16** | 3,1 | 1,50 | 0,9970 | 0,0180 | 0,0125 | 1,0000 | 1,0000 | 0,0000 |

---

## 3. Desempenho Global Agregado

| Métrica Global | Valor do FPM Puro | Critério do Plano | Interpretação |
| :--- | :---: | :---: | :--- |
| **$R^2$ Global** | **$0,9030$** | $> 0,8500$ | Boa reprodução das tendências qualitativas e hierarquia dos patamares. |
| **RMSE Global** | **$0,1010$** ($10,1\%$) | $< 0,1500$ | Erro quadrático médio moderado decorrente da hipótese de $\alpha$ estático. |
| **MAE Global** | **$0,0699$** ($6,99\%$) | $< 0,1000$ | Desvio absoluto médio uniforme de aproximadamente $7\%$ de conversão. |

---

## 4. Análise Físico-Química e Diagnóstico dos Desvios

A inspeção detalhada do comportamento do FPM Puro evidencia exatamente **por que a modelagem puramente fenomenológica é insuficiente** e justifica a transição para a **Modelagem Híbrida Serial**:

1. **Subestimação Sistemática para $\eta = 0,5$**:
   - No experimento real, mesmo sob forte escassez de ácido, a reação consome todo o reagente disponível até atingir $X_{\text{Zn}} \approx 0,50$.
   - O FPM com $\alpha_{\text{nominal}} = 5.500\,\mu\text{m/min}$ impõe parada artificial em $X_{\text{Zn}} = 0,5 \cdot [1 - 5500/23500] = 0,3830$, gerando um erro de patamar de $11,7\%$ em todos os 4 ensaios com $\eta = 0,5$.
2. **Subestimação do Patamar Neutro para $\eta = 1,0$**:
   - Os ensaios industriais de bancada atingem extração final entre $85\%$ e $87\%$.
   - O FPM nominal estaciona em $76,6\%$, deixando de capturar a dinâmica interfacial avançada que permite maior aproveitamento do reagente.
3. **Dispersão Cinética em Baixas Concentrações de Ácido ($C_{A0} = 0,10\,\text{mol/L}$)**:
   - Nos ensaios com $C_{A0} = 0,10\,\text{mol/L}$ (Ensaios 1, 6, 11 e 2), a relação líquido-sólido é muito maior (polpa mais diluída, $20\,\text{g/L}$ a $3\,\text{g/L}$).
   - O modelo FPM com parâmetros estáticos prevê uma aproximação lenta ao equilíbrio, ao passo que os dados experimentais mostram que mais de $80\%$ da dissolução ocorre nos primeiros $30$ segundos, resultando nos menores valores de $R^2$ ($0,53$ a $0,76$).
4. **Excelente Aderência sob Excesso de Ácido ($\eta = 1,5$ e $\eta = 3,1$)**:
   - Quando o ácido está em excesso moderado ou elevado, o termo de amortecimento torna-se secundário e o modelo atinge $R^2 > 0,97$ a $0,998$, comprovando a validade da reação química superficial como mecanismo governante.

---

## 5. Conclusão da Etapa
O baseline fenomenológico puro foi completamente estabelecido e validado com sucesso. Ele estabelece o ponto de partida do projeto ($R^2 = 0,9030$, $\text{RMSE} = 0,1010$), confirmando quantitativamente o espaço e a oportunidade de ganho preditivo que a inserção do estimador de Machine Learning ($v(t)$ via modelo caixa-preta) trará nas próximas etapas.
