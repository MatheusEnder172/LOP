# Item 5 — Problema inverso com integração exata

Gerado por `problema_inverso_malha_fina.py`. Os alvos novos não foram salvos em `Base de dados/processed/` nem usados em treino.

## Conferência

A malha de 0,25 min reproduz a Etapa 2.1: diferença máxima de 4,1 × 10^-6 no RMSE por ensaio e de 4,9 × 10^-5 nos parâmetros (os gravados têm 4 casas).

## O que muda ao trocar a integração

Mudança relativa |exata − malha|/|malha| nos 16 ensaios (mediana; máximo).

| Grandeza | Mudança |
| :-- | :-: |
| δ em 0,5 min | 1,9% (máx. 6,1%) |
| ν̄ de 0 a 0,5 min | 1,9% (máx. 6,1%) |
| ν nodal em 0,25 min | 23,1% (máx. 54,3%) |
| ν nodal em 0,5 min | 18,5% (máx. 63,4%) |

Em todos os pontos bem determinados: RMSE entre as duas versões de δ = 0,966 µm (96 pontos); de ν̄ = 1,230 µm/min (96 intervalos). Para comparação, o erro fora da dobra da v2 (Item 4) é de 7,72 µm em δ e 9,11 µm/min em ν̄.

De 0 a 0,5 min, ν̄ é δ(0,5)/0,5; por isso a mudança relativa é a mesma nas duas primeiras linhas da tabela.

## Reconstrução de X_Zn

- Malha de 0,25 min: RMSE global de 0,0137.
- Integração exata, reajustada: RMSE global de 0,0124.
- Parâmetros da malha integrados de forma exata, sem reajuste: RMSE global de 0,0743. Mostra que θ só vale junto com a regra de integração.
- Ensaios com a1, b1, a2 ou b2 no limite da faixa: 12 de 16 na malha e 12 de 16 na integração exata. Contando também c, cuja faixa é estreita (0 a 0,03): 16 e 16 de 16.

## Por ensaio

| Ensaio | η | C_A0 | RMSE X malha | RMSE X exata | RMSE X θ malha + exata | Dif. δ máx. (µm) | Dif. ν̄ máx. (µm/min) | ν(0,25) malha | ν(0,25) exata | ν̄(0 a 0,5) malha | ν̄(0 a 0,5) exata | Limites malha | Limites exata |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-- | :-- |
| 1 | 0,5 | 0,1 | 0,0095 | 0,0094 | 0,0918 | 0,05 | 0,18 | 8,3 | 5,6 | 6,8 | 6,9 | c | c |
| 2 | 3,1 | 0,1 | 0,0047 | 0,0047 | 0,0166 | 0,09 | 0,11 | 38,6 | 33,4 | 34,9 | 34,9 | c | c |
| 3 | 0,5 | 0,5 | 0,0094 | 0,0090 | 0,0951 | 0,06 | 0,22 | 9,3 | 6,1 | 7,7 | 7,8 | c | c |
| 4 | 0,5 | 1,0 | 0,0215 | 0,0202 | 0,1607 | 0,21 | 0,51 | 11,2 | 5,4 | 8,9 | 9,3 | a2,b2 | a2,b2 |
| 5 | 0,5 | 1,5 | 0,0122 | 0,0096 | 0,1722 | 0,20 | 0,46 | 10,7 | 4,9 | 8,5 | 8,9 | a2,b2,c | b1,a2,b2 |
| 6 | 1,0 | 0,1 | 0,0148 | 0,0132 | 0,0463 | 0,33 | 1,10 | 28,4 | 21,5 | 24,3 | 24,7 | b2,c | b2,c |
| 7 | 3,1 | 0,5 | 0,0073 | 0,0070 | 0,0150 | 0,45 | 1,10 | 51,3 | 43,2 | 46,5 | 46,7 | b2,c | b2,c |
| 8 | 1,0 | 0,5 | 0,0150 | 0,0141 | 0,0524 | 0,63 | 1,45 | 40,5 | 30,6 | 34,1 | 35,3 | a2,b2,c | c |
| 9 | 1,0 | 1,0 | 0,0113 | 0,0081 | 0,0591 | 0,87 | 1,92 | 39,6 | 28,6 | 33,0 | 34,8 | a2,b2,c | b2,c |
| 10 | 1,0 | 1,5 | 0,0167 | 0,0114 | 0,0646 | 0,99 | 2,39 | 38,8 | 26,5 | 32,3 | 34,3 | b2 | b2,c |
| 11 | 1,5 | 0,1 | 0,0256 | 0,0247 | 0,0367 | 5,60 | 1,20 | 42,0 | 32,8 | 36,1 | 37,3 | c | b1,b2,c |
| 12 | 3,1 | 1,0 | 0,0071 | 0,0071 | 0,0070 | 0,50 | 1,00 | 88,8 | 85,5 | 85,0 | 86,0 | a2,c | a2,c |
| 13 | 1,5 | 0,5 | 0,0125 | 0,0108 | 0,0189 | 1,33 | 3,58 | 62,3 | 50,3 | 54,8 | 55,7 | a2,c | a2,c |
| 14 | 1,5 | 1,0 | 0,0104 | 0,0104 | 0,0143 | 0,58 | 1,97 | 62,6 | 55,2 | 56,3 | 57,4 | a2,c | a2,c |
| 15 | 1,5 | 1,5 | 0,0090 | 0,0081 | 0,0155 | 1,21 | 3,35 | 61,2 | 51,4 | 54,3 | 55,2 | a2,c | a2,c |
| 16 | 3,1 | 1,5 | 0,0153 | 0,0142 | 0,0145 | 6,33 | 7,73 | 93,9 | 86,2 | 86,1 | 89,1 | a2,c | a2,c |

**Fora do escopo:** retreinar a rede com os alvos novos, o que exigiria refazer a busca, o comitê e consultar o teste cego de novo.
