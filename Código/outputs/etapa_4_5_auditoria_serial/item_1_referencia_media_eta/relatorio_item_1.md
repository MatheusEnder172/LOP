# Item 1 — Referências sem modelo

Gerado por `referencia_media_eta.py`. Nenhum modelo foi treinado e nenhuma escolha foi feita com o teste cego.

## Diferença entre a v2 e as referências

RMSE de X_Zn. Diferença negativa significa v2 melhor. O intervalo reamostra os 13 ensaios (10.000 réplicas).

| Conjunto | Versão | Referência | RMSE v2 | RMSE ref. | Diferença | IC 95% | Sementes em que a v2 ganha | Ensaios em que a v2 ganha |
| :-- | :-- | :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| CV | v2 (média das 10 sementes) | Média por η | 0,0326 | 0,0343 | -0,0017 | -0,0148 a 0,0105 | 7 de 10 | 7 de 13 |
| CV | v2 (curva média das 10 sementes) | Média por η | 0,0307 | 0,0343 | -0,0036 | -0,0176 a 0,0096 | — | 10 de 13 |
| Teste cego | v2 (comitê) | Média por η | 0,0202 | 0,0222 | -0,0020 | não calculado (3 ensaios) | — | 1 de 3 |
| CV | v2 (média das 10 sementes) | Interpolação em C_A0 | 0,0326 | 0,0323 | 0,0004 | -0,0130 a 0,0148 | 4 de 10 | 9 de 13 |
| CV | v2 (curva média das 10 sementes) | Interpolação em C_A0 | 0,0307 | 0,0323 | -0,0016 | -0,0171 a 0,0138 | — | 9 de 13 |
| Teste cego | v2 (comitê) | Interpolação em C_A0 | 0,0202 | 0,0180 | 0,0022 | não calculado (3 ensaios) | — | 1 de 3 |

## Leitura

- v2 (média das 10 sementes) × Média por η: o intervalo contém zero: com 13 ensaios, a v2 não é distinguível da referência nesta comparação.
- v2 (curva média das 10 sementes) × Média por η: o intervalo contém zero: com 13 ensaios, a v2 não é distinguível da referência nesta comparação.
- v2 (média das 10 sementes) × Interpolação em C_A0: o intervalo contém zero: com 13 ensaios, a v2 não é distinguível da referência nesta comparação.
- v2 (curva média das 10 sementes) × Interpolação em C_A0: o intervalo contém zero: com 13 ensaios, a v2 não é distinguível da referência nesta comparação.
- Teste cego: 3 ensaios não sustentam um intervalo por reamostragem; a diferença é só descritiva.
- A "curva média" tira a média de X_Zn entre as 10 sementes de cada dobra. É uma aproximação do comitê (que tira a média das taxas antes do balanço populacional), por isso não substitui a avaliação do comitê no teste cego.
- O RMSE global é dominado pelo patamar (6 dos 7 pontos de cada ensaio). O Item 2 separa o ponto de 0,5 min.

## RMSE por ensaio

| Conjunto | Ensaio | η | C_A0 (mol/L) | v2 | Média por η | Interpolação em C_A0 |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| CV | 1 | 0,5 | 0,1 | 0,0268 | 0,0267 | 0,0214 |
| CV | 2 | 3,1 | 0,1 | 0,0228 | 0,0687 | 0,0687 |
| CV | 3 | 0,5 | 0,5 | 0,0193 | 0,0169 | 0,0181 |
| CV | 4 | 0,5 | 1,0 | 0,0215 | 0,0295 | 0,0278 |
| CV | 5 | 0,5 | 1,5 | 0,0213 | 0,0207 | 0,0288 |
| CV | 6 | 1,0 | 0,1 | 0,0437 | 0,0448 | 0,0457 |
| CV | 9 | 1,0 | 1,0 | 0,0162 | 0,0248 | 0,0194 |
| CV | 10 | 1,0 | 1,5 | 0,0542 | 0,0235 | 0,0120 |
| CV | 11 | 1,5 | 0,1 | 0,0344 | 0,0468 | 0,0449 |
| CV | 12 | 3,1 | 1,0 | 0,0131 | 0,0189 | 0,0189 |
| CV | 13 | 1,5 | 0,5 | 0,0222 | 0,0215 | 0,0313 |
| CV | 15 | 1,5 | 1,5 | 0,0580 | 0,0276 | 0,0107 |
| CV | 16 | 3,1 | 1,5 | 0,0174 | 0,0369 | 0,0189 |
| Teste cego | 7 | 3,1 | 0,5 | 0,0217 | 0,0208 | 0,0116 |
| Teste cego | 8 | 1,0 | 0,5 | 0,0249 | 0,0191 | 0,0228 |
| Teste cego | 14 | 1,5 | 1,0 | 0,0113 | 0,0261 | 0,0177 |
