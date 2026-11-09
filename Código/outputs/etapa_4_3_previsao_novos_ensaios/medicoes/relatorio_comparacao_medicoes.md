# Comparação das medições dos 4 ensaios novos com a previsão a priori (09/11/2026)

A previsão (MLP v2, gerada em 08/11/2026 às 13h14, antes das medições) não foi alterada; seus arquivos foram conferidos por hash. As medições vêm de `Base de dados/Experimentos novos/Resultados.xlsx` (não alterado), com 6 instantes por ensaio (0,5; 1; 2; 3; 5 e 15 min; **não há medição em 4 min**).

## 1. Conversão das medições em X_Zn (hipóteses a confirmar)
A planilha dá a concentração de Zn (mg/L) = leitura × FD (FD = M2/M1), sem a conversão em X_Zn. Foi usada a mesma conta dos 16 ensaios originais: X_Zn = C_Zn · V / (m · w), com V = 0,200 L, m = 6,7; 12,1; 6,7 e 12,6 g (E1 a E4) e w = 0,611 ± 0,004 g de Zn por g de sólido (calibrado nos 16 ensaios originais). **Hipótese 1:** a planilha não registra uma diluição anterior; as concentrações só têm a ordem de grandeza esperada (16 a 35 g/L, contra 2 a 90 g/L nos originais) se o valor da coluna "Zn (mg/L)" for lido como g/L (isto é, com uma diluição anterior de 1000 vezes). Se o fator real for outro, todos os X_Zn mudam na mesma proporção.

## 2. Resultado como rotulado na planilha
| Ensaio | RMSE (v2) | X medido em 15 min | X previsto em 15 min | Limite min(1, η) |
| :-: | :-: | :-: | :-: | :-: |
| E1 | 0,144 | 0,81 | 0,71 | 0,75 |
| E2 | 0,402 | 0,54 | 0,93 | 1,00 |
| E3 | 0,626 | 1,69 | 0,99 | 1,00 |
| E4 | 0,041 | 0,45 | 0,40 | 0,40 |

Como rotulado, **E3 dá X_Zn = 1,69 (acima de 1, impossível)** e E2 dá 0,54, muito abaixo do previsto. As concentrações de Zn da planilha sugerem que **os rótulos E2 e E3 estão trocados** (ou as massas): o Zn do "E3" (34,6 g/L) só é possível com a massa de 12,1 g (E2), e o do "E2" (19,9 g/L), com 6,7 g (E3).

## 3. Resultado com E2 e E3 trocados (mais plausível; a confirmar com o laboratório)
| Ensaio | RMSE v2 | RMSE fenomenológico | RMSE v1 | RMSE interpolação | Viés (medido − v2) | X medido 15 min | X previsto 15 min |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| E1 | 0,144 | 0,081 | 0,146 | 0,173 | 0,140 | 0,81 | 0,71 |
| E2 | 0,049 | 0,117 | 0,043 | 0,031 | -0,037 | 0,94 | 0,93 |
| E3 | 0,042 | 0,072 | 0,061 | 0,031 | -0,036 | 0,97 | 0,99 |
| E4 | 0,041 | 0,036 | 0,062 | 0,042 | 0,041 | 0,45 | 0,40 |

RMSE global da v2: 0,081 nos 24 pontos; **0,044 sem o E1**; 50% dos pontos a menos de 0,05 da previsão. As referências de erro do modelo eram 0,033 (validação cruzada) e 0,020 (teste cego).

X_Zn medido:

| t (min) | E1 | E2 | E3 | E4 |
| :-: | :-: | :-: | :-: | :-: |
| 0,5 | 0,769 | 0,834 | 0,879 | 0,416 |
| 1,0 | 0,867 | 0,853 | 0,896 | 0,429 |
| 2,0 | 0,844 | 0,869 | 0,973 | 0,437 |
| 3,0 | 0,824 | 0,878 | 0,942 | 0,440 |
| 5,0 | 0,813 | 0,936 | 0,967 | 0,439 |
| 15,0 | 0,809 | 0,936 | 0,971 | 0,448 |

X_Zn previsto (v2):

| t (min) | E1 | E2 | E3 | E4 |
| :-: | :-: | :-: | :-: | :-: |
| 0,5 | 0,616 | 0,889 | 0,923 | 0,365 |
| 1,0 | 0,667 | 0,923 | 0,970 | 0,398 |
| 2,0 | 0,688 | 0,929 | 0,985 | 0,400 |
| 3,0 | 0,698 | 0,929 | 0,988 | 0,400 |
| 5,0 | 0,707 | 0,929 | 0,989 | 0,400 |
| 15,0 | 0,713 | 0,929 | 0,989 | 0,400 |

## 4. Leitura
- **E2 e E3 (η = 1,25 e 2,25):** o patamar é bem previsto (diferença de 0,007 e -0,018 em 15 min), e o erro vem sobretudo dos instantes iniciais (em 0,5 e 1 min, a previsão fica 0,04 a 0,07 acima do medido). O modelo híbrido foi melhor que o fenomenológico nesses dois, mas a **interpolação simples dos 16 ensaios medidos foi ainda um pouco melhor** (RMSE 0,031 e 0,031), o que limita o que se pode afirmar sobre o ganho do modelo dentro do domínio.
- **E1 e E4 (C_A0 = 0,25 mol/L; η = 0,75 e 0,40):** em **todos** os instantes, o X_Zn medido fica **acima do limite estequiométrico** (E1: 0,77 a 0,87 contra 0,75; E4: 0,42 a 0,45 contra 0,40). Com as condições nominais isso é impossível, então o desvio (E1: RMSE 0,144) não pode ser atribuído ao modelo antes de se esclarecer o dado. Em E1 o X medido ainda cai de 0,87 (1 min) para 0,81 (15 min), o que não é esperado para uma conversão.
- Hipóteses, **não testadas**, para o excesso nos dois ensaios de menor C_A0: concentração real do ácido maior que 0,25 mol/L, massa ou volume diferentes dos nominais, teor de Zn do sólido diferente (w), ou viés analítico ou de diluição. Um ajuste exploratório do fator de escala em C_A0 e η dá s = 1,11 para E4 (RMSE 0,009) mas s > 1,3 para E1, ou seja, uma única correção de ácido não explicaria os dois.
- Efeito do volume (200 contra 400 mL): não é possível separá-lo dos problemas acima.

## 5. Arquivos
`Base de dados/Experimentos novos/medicoes_XZn_ensaios_novos.csv`; em `Código/outputs/etapa_4_3_previsao_novos_ensaios/` as tabelas `tabela_comparacao_medicoes*.csv` e as figuras `*_com_medicoes` (como rotulado); em `medicoes/`: `medicoes_convertidas_todas.csv`, `tabela_sensibilidade_comparacao.csv` (rótulos e w ± 0,02), `fig_ne_07_rotulagem_E2_E3` e `fig_ne_08_painel_medicoes_E2_E3_trocados`.
