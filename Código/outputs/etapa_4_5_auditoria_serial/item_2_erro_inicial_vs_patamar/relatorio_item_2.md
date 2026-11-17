# Item 2 — Onde está o erro: 0,5 min contra o patamar

Gerado por `erro_por_faixa_de_tempo.py`. Nenhum modelo foi treinado e nenhuma escolha foi feita com o teste cego.

Em 0,5 min a conversão medida já é, em média, 93% da conversão em 15 min.

## Erro por faixa de tempo

RMSE de X_Zn; entre parênteses, o erro médio com sinal (previsto − medido). Modelos com sementes: média das 10 sementes.

### Validação cruzada (13 ensaios)

| Faixa | n | v2 | MLP pura | Média por η | Interpolação em C_A0 | Fenomenológico |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 min | 13 | 0,0443 (-0,0287) | 0,0618 (0,0147) | 0,0654 (0,0079) | 0,0562 (0,0191) | 0,0644 (0,0394) |
| 1 a 3 min | 39 | 0,0299 (-0,0064) | 0,0438 (-0,0071) | 0,0334 (0,0013) | 0,0335 (0,0068) | 0,0687 (0,0501) |
| 4 a 15 min | 39 | 0,0305 (-0,0154) | 0,0347 (-0,0032) | 0,0145 (0,0012) | 0,0158 (0,0001) | 0,0690 (0,0418) |
| Todos | 91 | 0,0326 (-0,0135) | 0,0437 (-0,0023) | 0,0343 (0,0022) | 0,0323 (0,0057) | 0,0682 (0,0450) |

### Teste cego (3 ensaios; só descritivo)

| Faixa | n | v2 | MLP pura | Média por η | Interpolação em C_A0 | Fenomenológico |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 min | 3 | 0,0334 (0,0042) | 0,0255 (-0,0090) | 0,0278 (0,0011) | 0,0259 (-0,0124) | 0,0940 (0,0923) |
| 1 a 3 min | 9 | 0,0164 (0,0041) | 0,0144 (-0,0035) | 0,0256 (-0,0141) | 0,0182 (-0,0123) | 0,0770 (0,0643) |
| 4 a 15 min | 9 | 0,0175 (-0,0106) | 0,0191 (-0,0157) | 0,0153 (-0,0111) | 0,0141 (-0,0102) | 0,0730 (0,0514) |
| Todos | 21 | 0,0202 (-0,0022) | 0,0184 (-0,0095) | 0,0222 (-0,0106) | 0,0180 (-0,0114) | 0,0780 (0,0628) |

## A v2 ganha em 0,5 min?

Validação cruzada. Diferença negativa significa v2 melhor. O intervalo reamostra os 13 ensaios.

| Faixa | Comparador | RMSE v2 | RMSE comparador | Diferença | IC 95% | Sementes em que a v2 ganha | Ensaios em que a v2 ganha |
| :-- | :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 min | MLP pura | 0,0443 | 0,0618 | -0,0174 | -0,0449 a 0,0173 | 10 de 10 | 5 de 13 |
| 0,5 min | Média por η | 0,0443 | 0,0654 | -0,0210 | -0,0488 a 0,0073 | 10 de 10 | 9 de 13 |
| 0,5 min | Interpolação em C_A0 | 0,0443 | 0,0562 | -0,0119 | -0,0434 a 0,0229 | 10 de 10 | 6 de 13 |
| 0,5 min | Fenomenológico | 0,0443 | 0,0644 | -0,0201 | -0,0362 a -0,0042 | 10 de 10 | 8 de 13 |
| 1 a 3 min | MLP pura | 0,0299 | 0,0438 | -0,0139 | -0,0209 a -0,0063 | 10 de 10 | 11 de 13 |
| 1 a 3 min | Média por η | 0,0299 | 0,0334 | -0,0035 | -0,0116 a 0,0046 | 7 de 10 | 9 de 13 |
| 1 a 3 min | Interpolação em C_A0 | 0,0299 | 0,0335 | -0,0036 | -0,0127 a 0,0063 | 7 de 10 | 10 de 13 |
| 1 a 3 min | Fenomenológico | 0,0299 | 0,0687 | -0,0388 | -0,0650 a -0,0092 | 10 de 10 | 11 de 13 |
| 4 a 15 min | MLP pura | 0,0305 | 0,0347 | -0,0042 | -0,0103 a 0,0008 | 7 de 10 | 9 de 13 |
| 4 a 15 min | Média por η | 0,0305 | 0,0145 | 0,0160 | 0,0029 a 0,0276 | 0 de 10 | 4 de 13 |
| 4 a 15 min | Interpolação em C_A0 | 0,0305 | 0,0158 | 0,0147 | 0,0001 a 0,0275 | 0 de 10 | 3 de 13 |
| 4 a 15 min | Fenomenológico | 0,0305 | 0,0690 | -0,0385 | -0,0676 a -0,0014 | 10 de 10 | 9 de 13 |
| Todos | MLP pura | 0,0326 | 0,0437 | -0,0110 | -0,0205 a -0,0017 | 10 de 10 | 10 de 13 |
| Todos | Média por η | 0,0326 | 0,0343 | -0,0017 | -0,0148 a 0,0104 | 7 de 10 | 7 de 13 |
| Todos | Interpolação em C_A0 | 0,0326 | 0,0323 | 0,0004 | -0,0133 a 0,0145 | 4 de 10 | 9 de 13 |
| Todos | Fenomenológico | 0,0326 | 0,0682 | -0,0356 | -0,0600 a -0,0066 | 10 de 10 | 10 de 13 |

## Leitura

- v2 × MLP pura: o intervalo contém zero; com 13 ensaios, não dá para distinguir os dois em 0,5 min.
- v2 × Média por η: o intervalo contém zero; com 13 ensaios, não dá para distinguir os dois em 0,5 min.
- v2 × Interpolação em C_A0: o intervalo contém zero; com 13 ensaios, não dá para distinguir os dois em 0,5 min.
- v2 × Fenomenológico: o erro da v2 em 0,5 min é menor, e o intervalo não contém zero.
- Em 0,5 min há um único ponto por ensaio (13 na validação cruzada), o que limita a precisão do intervalo.

## Efeito de C_A0 em 0,5 min

Previsões fora da amostra: validação cruzada nos 13 ensaios de treino e comitê congelado nos 3 de teste cego. Modelos com sementes entram pela média das previsões.

| η | C_A0 (mol/L) | Conjunto | Medição | v2 | MLP pura | Média por η | Interpolação em C_A0 | Fenomenológico |
| :-: | :-: | :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| 0,5 | 0,1 | CV | 0,420 | 0,456 | 0,470 | 0,475 | 0,450 | 0,488 |
| 0,5 | 0,5 | CV | 0,450 | 0,436 | 0,458 | 0,470 | 0,456 | 0,500 |
| 0,5 | 1,0 | CV | 0,500 | 0,484 | 0,487 | 0,453 | 0,470 | 0,500 |
| 0,5 | 1,5 | CV | 0,490 | 0,458 | 0,618 | 0,475 | 0,500 | 0,500 |
| 1,0 | 0,1 | CV | 0,750 | 0,706 | 0,716 | 0,835 | 0,830 | 0,724 |
| 1,0 | 0,5 | Teste cego | 0,830 | 0,790 | 0,788 | 0,807 | 0,786 | 0,904 |
| 1,0 | 1,0 | CV | 0,830 | 0,808 | 0,828 | 0,795 | 0,808 | 0,944 |
| 1,0 | 1,5 | CV | 0,840 | 0,757 | 0,811 | 0,790 | 0,830 | 0,959 |
| 1,5 | 0,1 | CV | 0,860 | 0,818 | 0,845 | 0,915 | 0,920 | 0,795 |
| 1,5 | 0,5 | CV | 0,920 | 0,867 | 0,881 | 0,885 | 0,874 | 0,978 |
| 1,5 | 1,0 | Teste cego | 0,910 | 0,924 | 0,925 | 0,897 | 0,915 | 0,997 |
| 1,5 | 1,5 | CV | 0,910 | 0,852 | 0,900 | 0,890 | 0,920 | 1,000 |
| 3,1 | 0,1 | CV | 0,820 | 0,821 | 0,950 | 0,980 | 0,980 | 0,854 |
| 3,1 | 0,5 | Teste cego | 0,880 | 0,919 | 0,880 | 0,920 | 0,882 | 0,996 |
| 3,1 | 1,0 | CV | 0,960 | 0,942 | 0,972 | 0,980 | 0,980 | 1,000 |
| 3,1 | 1,5 | CV | 0,980 | 0,951 | 0,985 | 0,890 | 0,960 | 1,000 |

### Resumo do efeito de C_A0

Subida de X_Zn de C_A0 = 0,1 para a média de 0,5 e 1,0 mol/L. O "erro no efeito" compara o desvio de X_Zn em relação à média da própria η.

| Fonte | η = 0,5 | η = 1 | η = 1,5 | η = 3,1 | η com o sinal da medição | Erro no efeito de C_A0 | Correlação |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| Medição | 0,055 | 0,080 | 0,055 | 0,100 | — | — | — |
| v2 | 0,004 | 0,093 | 0,077 | 0,109 | 4 de 4 | 0,0256 | 0,80 |
| MLP pura | 0,002 | 0,092 | 0,058 | -0,024 | 3 de 4 | 0,0400 | 0,59 |
| Média por η | -0,013 | -0,034 | -0,024 | -0,030 | 0 de 4 | 0,0578 | -0,57 |
| Interpolação em C_A0 | 0,013 | -0,033 | -0,025 | -0,049 | 1 de 4 | 0,0476 | 0,07 |
| Fenomenológico | 0,012 | 0,200 | 0,193 | 0,144 | 4 de 4 | 0,0490 | 0,74 |

A média por η não tem como representar C_A0. A correlação dela fica distorcida porque cada ensaio é retirado da própria média: ensaios acima da média recebem uma previsão mais baixa.
